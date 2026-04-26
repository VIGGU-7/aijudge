from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Form
from starlette.responses import Response as StarletteResponse
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os, logging, bcrypt, jwt, uuid, json, io
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

import gemini_client
import repo_fetcher
import ppt_parser
import context_builder
import video_pipeline
import report_generator

# WhisperModel will be initialized below

# ── Config ──────────────────────────────────────────────────────
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def verify_password(plain, hashed):
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_access_token(uid, email):
    return jwt.encode({"sub": uid, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "type": "access"}, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(uid):
    return jwt.encode({"sub": uid, "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS), "type": "refresh"}, get_jwt_secret(), algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(401, "User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

async def require_role(request, roles):
    user = await get_current_user(request)
    if user.get("role") not in roles:
        raise HTTPException(403, "Insufficient permissions")
    return user

# ── Lifespan ────────────────────────────────────────────────────
async def create_indexes():
    await db.users.create_index("email", unique=True)
    await db.hackathons.create_index("status")
    await db.teams.create_index("hackathon_id")
    await db.viva_sessions.create_index([("team_id", 1), ("created_at", -1)])
    await db.context_profiles.create_index("team_id", unique=True)
    await db.evaluations.create_index([("hackathon_id", 1), ("team_id", 1)])
    await db.telemetry_logs.create_index("team_id")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    yield
    client.close()

app = FastAPI(lifespan=lifespan)
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize faster-whisper model globally so it's loaded only once
import tempfile
from faster_whisper import WhisperModel
try:
    logger.info("Loading WhisperModel('base')...")
    whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    logger.info("WhisperModel loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load WhisperModel: {e}")
    whisper_model = None

ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"}

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")

    # Handle preflight
    if request.method == "OPTIONS":
        resp = StarletteResponse(status_code=204)
        if origin in ALLOWED_ORIGINS:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Cookie"
            resp.headers["Access-Control-Max-Age"] = "600"
        return resp

    # Handle normal requests
    try:
        response = await call_next(request)
    except Exception:
        import traceback; traceback.print_exc()
        response = StarletteResponse(status_code=500, content='{"detail":"Internal Server Error"}', media_type="application/json")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response

# ── Models ──────────────────────────────────────────────────────
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "participant"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class HackathonCreate(BaseModel):
    name: str
    description: str
    start_time: str
    end_time: str
    max_team_size: int = 4

class TeamCreate(BaseModel):
    name: str
    hackathon_id: str
    github_repo: Optional[str] = None

class ProjectInfoSubmit(BaseModel):
    github_url: Optional[str] = None
    features: List[str] = []
    tech_stack: List[str] = []
    project_description: str = ""

class VivaStartRequest(BaseModel):
    team_id: str
    category: str = "code_deep_dive"

class VivaAnswerSubmit(BaseModel):
    session_id: str
    question_id: str
    answer: str

class MentorChatRequest(BaseModel):
    message: str
    session_id: str
    code_context: Optional[str] = None

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"

class EvaluationCreate(BaseModel):
    team_id: str
    hackathon_id: str
    scores: Dict[str, float]
    notes: Optional[str] = None

WEIGHTS = {"innovation": 0.2, "complexity": 0.15, "impact": 0.15, "originality": 0.2, "execution": 0.15, "presentation": 0.15}

def calc_score(scores):
    return round(sum(float(scores.get(k, 0)) * w for k, w in WEIGHTS.items()), 2)

# ── AUTH ─────────────────────────────────────────────────────────
@api.post("/auth/register")
async def register(data: UserRegister, response: Response):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    doc = {"email": email, "password_hash": hash_password(data.password), "name": data.name, "role": data.role if data.role in ["participant", "organizer"] else "participant", "created_at": datetime.now(timezone.utc).isoformat()}
    result = await db.users.insert_one(doc)
    uid = str(result.inserted_id)
    response.set_cookie("access_token", create_access_token(uid, email), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", create_refresh_token(uid), httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return {"id": uid, "email": email, "name": data.name, "role": doc["role"]}

@api.post("/auth/login")
async def login(creds: UserLogin, response: Response):
    email = creds.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(creds.password, user["password_hash"]):
        raise HTTPException(401, "Invalid credentials")
    uid = str(user["_id"])
    response.set_cookie("access_token", create_access_token(uid, email), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
    response.set_cookie("refresh_token", create_refresh_token(uid), httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    return {"id": uid, "email": email, "name": user["name"], "role": user["role"]}

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}

@api.get("/auth/me")
async def get_me(request: Request):
    return await get_current_user(request)

@api.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(401, "No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(401, "Invalid token")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(401, "User not found")
        response.set_cookie("access_token", create_access_token(str(user["_id"]), user["email"]), httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Refreshed"}
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

# ── HACKATHONS ───────────────────────────────────────────────────
@api.post("/hackathons")
async def create_hackathon(data: HackathonCreate, request: Request):
    user = await require_role(request, ["admin", "organizer"])
    doc = {**data.model_dump(), "status": "active", "organizer_id": user["_id"], "created_at": datetime.now(timezone.utc).isoformat()}
    r = await db.hackathons.insert_one(doc)
    doc.pop("_id", None)
    return {"id": str(r.inserted_id), **doc}

@api.patch("/hackathons/{hid}/status")
async def update_hackathon_status(hid: str, request: Request):
    await require_role(request, ["admin", "organizer"])
    body = await request.json()
    new_status = body.get("status", "")
    if new_status not in ["draft", "active", "completed"]:
        raise HTTPException(400, "Status must be draft, active, or completed")
    await db.hackathons.update_one({"_id": ObjectId(hid)}, {"$set": {"status": new_status}})
    return {"message": f"Status updated to {new_status}"}

@api.get("/hackathons")
async def list_hackathons(status: Optional[str] = None):
    q = {"status": status} if status else {}
    out = []
    async for h in db.hackathons.find(q):
        h["id"] = str(h["_id"]); del h["_id"]; out.append(h)
    return out

@api.get("/hackathons/{hid}")
async def get_hackathon(hid: str):
    h = await db.hackathons.find_one({"_id": ObjectId(hid)})
    if not h: raise HTTPException(404, "Not found")
    h["id"] = str(h["_id"]); del h["_id"]; return h

# ── TEAMS ────────────────────────────────────────────────────────
@api.post("/teams")
async def create_team(data: TeamCreate, request: Request):
    user = await get_current_user(request)
    doc = {"name": data.name, "hackathon_id": data.hackathon_id, "github_repo": data.github_repo, "members": [{"user_id": user["_id"], "name": user["name"], "role": "leader"}], "created_at": datetime.now(timezone.utc).isoformat()}
    r = await db.teams.insert_one(doc)
    doc.pop("_id", None)
    return {"id": str(r.inserted_id), **doc}

# IMPORTANT: /teams/my/current MUST be before /teams/{tid}
@api.get("/teams/my/current")
async def get_my_team(request: Request, hackathon_id: Optional[str] = None):
    user = await get_current_user(request)
    q = {"members.user_id": user["_id"]}
    if hackathon_id: q["hackathon_id"] = hackathon_id
    t = await db.teams.find_one(q)
    if not t: return None
    t["id"] = str(t["_id"]); del t["_id"]; return t

@api.get("/teams/search")
async def search_teams(query: str = ""):
    if not query:
        return []
    out = []
    async for t in db.teams.find({"name": {"$regex": query, "$options": "i"}}):
        t["id"] = str(t["_id"])
        del t["_id"]
        out.append(t)
    return out

@api.get("/teams")
async def list_teams(hackathon_id: Optional[str] = None):
    q = {"hackathon_id": hackathon_id} if hackathon_id else {}
    out = []
    async for t in db.teams.find(q):
        t["id"] = str(t["_id"]); del t["_id"]; out.append(t)
    return out

@api.get("/teams/{tid}")
async def get_team(tid: str):
    t = await db.teams.find_one({"_id": ObjectId(tid)})
    if not t: raise HTTPException(404, "Not found")
    t["id"] = str(t["_id"]); del t["_id"]; return t

@api.post("/teams/{tid}/join")
async def join_team(tid: str, request: Request):
    user = await get_current_user(request)
    team = await db.teams.find_one({"_id": ObjectId(tid)})
    if not team: raise HTTPException(404, "Not found")
    # Check if already a member
    existing = [m for m in team.get("members", []) if m.get("user_id") == user["_id"]]
    if existing:
        return {"message": "Already a member"}
    await db.teams.update_one({"_id": ObjectId(tid)}, {"$push": {"members": {"user_id": user["_id"], "name": user["name"], "role": "member"}}})
    return {"message": "Joined"}

@api.post("/teams/{tid}/add-member")
async def add_member_to_team(tid: str, request: Request):
    """Add a user to the team by email (organizer or team leader)."""
    await get_current_user(request)
    body = await request.json()
    email = body.get("email", "").lower()
    if not email:
        raise HTTPException(400, "Email is required")
    user_to_add = await db.users.find_one({"email": email})
    if not user_to_add:
        raise HTTPException(404, f"No user found with email: {email}")
    team = await db.teams.find_one({"_id": ObjectId(tid)})
    if not team:
        raise HTTPException(404, "Team not found")
    uid = str(user_to_add["_id"])
    existing = [m for m in team.get("members", []) if m.get("user_id") == uid]
    if existing:
        return {"message": "User is already a member"}
    await db.teams.update_one({"_id": ObjectId(tid)}, {"$push": {"members": {"user_id": uid, "name": user_to_add["name"], "role": "member"}}})
    return {"message": f"{user_to_add['name']} added to the team"}

# ── CONTEXT BUILDING (Project Setup) ────────────────────────────
@api.post("/teams/{tid}/project-info")
async def submit_project_info(tid: str, data: ProjectInfoSubmit, request: Request):
    """Submit project info: GitHub URL, features, tech stack, description."""
    user = await get_current_user(request)
    doc = {"team_id": tid, "user_id": user["_id"], **data.model_dump(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.project_info.update_one({"team_id": tid}, {"$set": doc}, upsert=True)
    if data.github_url:
        await db.teams.update_one({"_id": ObjectId(tid)}, {"$set": {"github_repo": data.github_url}})
    return {"message": "Project info saved"}

@api.get("/teams/{tid}/project-info")
async def get_project_info(tid: str, request: Request):
    await get_current_user(request)
    doc = await db.project_info.find_one({"team_id": tid})
    if not doc:
        return None
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

@api.post("/teams/{tid}/upload-ppt")
async def upload_ppt(tid: str, request: Request, file: UploadFile = File(...)):
    """Upload PPT/PDF for AI analysis."""
    await get_current_user(request)
    if not file.filename:
        raise HTTPException(400, "No file selected")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Uploaded file is empty")
    parsed = ppt_parser.parse_file(content, file.filename)
    if parsed.get("error"):
        raise HTTPException(400, parsed["error"])
    await db.ppt_data.update_one({"team_id": tid}, {"$set": {"team_id": tid, "filename": file.filename, "parsed": parsed, "created_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {
        "message": "PPT uploaded",
        "slides_count": parsed.get("total_slides", 0),
        "filename": file.filename,
        "format": parsed.get("format"),
    }

@api.get("/teams/{tid}/ppt")
async def get_uploaded_ppt(tid: str, request: Request):
    await get_current_user(request)
    doc = await db.ppt_data.find_one({"team_id": tid})
    if not doc:
        return None
    parsed = doc.get("parsed", {})
    return {
        "id": str(doc["_id"]),
        "team_id": tid,
        "filename": doc.get("filename"),
        "slides_count": parsed.get("total_slides", 0),
        "format": parsed.get("format"),
        "created_at": doc.get("created_at"),
    }

@api.post("/teams/{tid}/build-context")
async def build_context(tid: str, request: Request):
    """Trigger context profile building from repo + PPT + user info."""
    await get_current_user(request)
    project_info = await db.project_info.find_one({"team_id": tid})
    ppt_doc = await db.ppt_data.find_one({"team_id": tid})

    repo_data = None
    github_url = project_info.get("github_url") if project_info else None
    if github_url:
        repo_data = await repo_fetcher.fetch_repo(github_url)

    ppt_data = ppt_doc.get("parsed") if ppt_doc else None
    user_input = {"features": project_info.get("features", []) if project_info else [], "tech_stack": project_info.get("tech_stack", []) if project_info else [], "project_description": project_info.get("project_description", "") if project_info else ""}

    has_user_input = bool(github_url or user_input["features"] or user_input["tech_stack"] or user_input["project_description"].strip())
    if not has_user_input and not ppt_data:
        raise HTTPException(400, "Add project info or upload a PPT/PDF before building the AI context profile")

    profile = await context_builder.build_profile(repo_data, ppt_data, user_input)

    await db.context_profiles.update_one({"team_id": tid}, {"$set": {"team_id": tid, "profile": profile, "created_at": datetime.now(timezone.utc).isoformat()}}, upsert=True)
    return {"message": "Context profile built", "profile": profile}

@api.get("/teams/{tid}/context-profile")
async def get_context_profile(tid: str, request: Request):
    await get_current_user(request)
    doc = await db.context_profiles.find_one({"team_id": tid})
    if not doc: return None
    doc["id"] = str(doc["_id"]); del doc["_id"]; return doc

# ── AI VIVA ──────────────────────────────────────────────────────
@api.post("/ai/viva/start")
async def start_viva(data: VivaStartRequest, request: Request):
    user = await get_current_user(request)
    ctx_doc = await db.context_profiles.find_one({"team_id": data.team_id})
    ctx_profile = ctx_doc.get("profile", {}) if ctx_doc else {}

    question = await gemini_client.generate_viva_question(ctx_profile, data.category)
    sid = str(uuid.uuid4())
    qid = str(uuid.uuid4())
    question["id"] = qid

    await db.viva_sessions.insert_one({"session_id": sid, "team_id": data.team_id, "user_id": user["_id"], "questions": [question], "status": "in_progress", "created_at": datetime.now(timezone.utc).isoformat()})
    return {"session_id": sid, "question": question, "question_number": 1, "total_questions": 5}

VIVA_MAX_QUESTIONS = 5

@api.post("/ai/viva/next-question")
async def next_viva_question(data: VivaStartRequest, request: Request, session_id: str = ""):
    await get_current_user(request)
    ctx_doc = await db.context_profiles.find_one({"team_id": data.team_id})
    ctx_profile = ctx_doc.get("profile", {}) if ctx_doc else {}

    prev_questions = []
    current_count = 0
    if session_id:
        sess = await db.viva_sessions.find_one({"session_id": session_id})
        if sess:
            prev_questions = [q.get("question", "") for q in sess.get("questions", [])]
            current_count = len(sess.get("questions", []))

    if current_count >= VIVA_MAX_QUESTIONS:
        raise HTTPException(400, "Maximum of 5 questions reached. Session complete.")

    question = await gemini_client.generate_viva_question(ctx_profile, data.category, prev_questions)
    qid = str(uuid.uuid4())
    question["id"] = qid

    if session_id:
        await db.viva_sessions.update_one({"session_id": session_id}, {"$push": {"questions": question}})
    return {"question": question, "question_number": current_count + 1, "total_questions": VIVA_MAX_QUESTIONS}

@api.post("/ai/viva/answer")
async def submit_viva_answer(data: VivaAnswerSubmit, request: Request):
    await get_current_user(request)
    sess = await db.viva_sessions.find_one({"session_id": data.session_id})
    if not sess: raise HTTPException(404, "Session not found")

    question = next((q for q in sess["questions"] if q.get("id") == data.question_id), None)
    if not question: raise HTTPException(404, "Question not found")

    ctx_doc = await db.context_profiles.find_one({"team_id": sess["team_id"]})
    ctx_profile = ctx_doc.get("profile", {}) if ctx_doc else {}

    evaluation = await gemini_client.evaluate_viva_answer(question, data.answer, ctx_profile)

    await db.viva_sessions.update_one({"session_id": data.session_id, "questions.id": data.question_id}, {"$set": {"questions.$.answer": data.answer, "questions.$.evaluation": evaluation}})

    # Count how many questions have been answered
    answered_count = sum(1 for q in sess["questions"] if q.get("answer")) + 1  # +1 for current
    total_qs = len(sess["questions"])
    is_complete = answered_count >= VIVA_MAX_QUESTIONS

    if is_complete:
        await db.viva_sessions.update_one({"session_id": data.session_id}, {"$set": {"status": "completed"}})

    evaluation["question_number"] = answered_count
    evaluation["total_questions"] = VIVA_MAX_QUESTIONS
    evaluation["completed"] = is_complete
    return evaluation

@api.get("/ai/viva/sessions/{tid}")
async def get_viva_sessions(tid: str, request: Request):
    await get_current_user(request)
    out = []
    async for s in db.viva_sessions.find({"team_id": tid}).sort("created_at", -1):
        s["id"] = str(s["_id"]); del s["_id"]; out.append(s)
    return out

# ── PLAGIARISM DETECTION (Organizer-only) ─────────────────────────
CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".rb", ".php", ".cs", ".swift", ".kt", ".html", ".css", ".sql"}
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build", ".next", "vendor"}

@api.post("/plagiarism/check")
async def run_plagiarism_check(request: Request):
    """Clone a GitHub repo, extract code files, run Gemini plagiarism analysis."""
    user = await get_current_user(request)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(403, "Only organizers can run plagiarism checks")

    body = await request.json()
    team_id = body.get("team_id", "")
    repo_url = body.get("repo_url", "")
    if not team_id or not repo_url:
        raise HTTPException(400, "team_id and repo_url are required")

    import subprocess, shutil
    clone_dir = os.path.join(tempfile.gettempdir(), f"plag_{uuid.uuid4().hex[:8]}")
    try:
        # Clone repo (shallow, timeout 30s)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, clone_dir],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(400, f"Failed to clone repo: {result.stderr[:200]}")

        # Extract code files
        code_files = {}
        for root, dirs, files in os.walk(clone_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in CODE_EXTENSIONS:
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, clone_dir)
                    try:
                        with open(fpath, "r", errors="ignore") as f:
                            content = f.read()
                        if len(content.strip()) > 20:  # skip near-empty files
                            code_files[rel_path] = content
                    except Exception:
                        pass

        if not code_files:
            raise HTTPException(400, "No code files found in the repository")

        # Run Gemini plagiarism analysis
        analysis = await gemini_client.analyze_plagiarism(code_files)

        # Store result in DB
        report = {
            "team_id": team_id,
            "repo_url": repo_url,
            "overall_score": analysis.get("overall_score", 0),
            "risk_level": analysis.get("risk_level", "unknown"),
            "summary": analysis.get("summary", ""),
            "files": analysis.get("files", []),
            "checked_by": str(user["_id"]),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "files_analyzed": len(code_files),
        }
        # Upsert: replace old report for same team
        await db.plagiarism_reports.update_one(
            {"team_id": team_id},
            {"$set": report},
            upsert=True
        )
        return report
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Plagiarism check error: {exc}")
        raise HTTPException(500, f"Plagiarism check failed: {exc}")
    finally:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)

@api.get("/plagiarism/reports")
async def list_plagiarism_reports(request: Request):
    """List all plagiarism reports (organizer-only)."""
    user = await get_current_user(request)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(403, "Only organizers can view plagiarism reports")
    out = []
    async for r in db.plagiarism_reports.find().sort("checked_at", -1):
        r["id"] = str(r["_id"]); del r["_id"]
        out.append(r)
    return out

@api.get("/plagiarism/reports/{team_id}")
async def get_plagiarism_report(team_id: str, request: Request):
    """Get plagiarism report for a specific team (organizer-only)."""
    user = await get_current_user(request)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(403, "Only organizers can view plagiarism reports")
    doc = await db.plagiarism_reports.find_one({"team_id": team_id})
    if not doc:
        return None
    doc["id"] = str(doc["_id"]); del doc["_id"]
    return doc

# ── AI: Code Analysis, Plagiarism, Mentor ────────────────────────
@api.post("/ai/analyze-code")
async def analyze_code(data: CodeAnalysisRequest, request: Request):
    await get_current_user(request)
    return await gemini_client.analyze_code_quality(data.code, data.language)

@api.post("/ai/plagiarism-check")
async def plagiarism_check(request: Request, team_id: str = "", code: str = ""):
    await get_current_user(request)
    result = await gemini_client.check_plagiarism(code)
    if team_id:
        await db.plagiarism_reports.insert_one({"team_id": team_id, "result": result, "created_at": datetime.now(timezone.utc).isoformat()})
    return result

@api.post("/ai/mentor/chat")
async def mentor_chat_route(data: MentorChatRequest, request: Request):
    user = await get_current_user(request)
    response = await gemini_client.mentor_chat(data.message, data.code_context)
    await db.messages.insert_one({"session_id": data.session_id, "user_id": user["_id"], "role": "user", "content": data.message, "created_at": datetime.now(timezone.utc).isoformat()})
    await db.messages.insert_one({"session_id": data.session_id, "user_id": "ai", "role": "assistant", "content": response, "created_at": datetime.now(timezone.utc).isoformat()})
    return {"response": response}

@api.post("/ai/transcribe-audio")
async def transcribe_audio_route(request: Request, file: UploadFile = File(...)):
    await get_current_user(request)
    if not file.filename:
        raise HTTPException(400, "No audio file selected")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Uploaded audio file is empty")
    try:
        transcript = await gemini_client.transcribe_audio(content, file.filename, file.content_type)
    except Exception as exc:
        raise HTTPException(500, f"Audio transcription failed: {exc}")
    if not transcript:
        raise HTTPException(400, "No transcript could be generated from the recording")
    return {"transcript": transcript}

@api.post("/transcribe")
async def transcribe_faster_whisper(request: Request, file: UploadFile = File(...)):
    await get_current_user(request)
    if not whisper_model:
        raise HTTPException(500, "Whisper model not initialized")
    if not file.filename:
        raise HTTPException(400, "No audio file selected")
    content = await file.read()
    if not content or len(content) < 1000:
        return {"transcript": ""}
    
    suffix = os.path.splitext(file.filename)[1] or ".webm"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        segments, info = whisper_model.transcribe(temp_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return {"transcript": text.strip()}
    except Exception as exc:
        logger.error(f"Faster-whisper error: {exc}")
        raise HTTPException(500, f"Transcription failed: {exc}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@api.get("/ai/mentor/history/{session_id}")
async def mentor_history(session_id: str, request: Request):
    await get_current_user(request)
    out = []
    async for m in db.messages.find({"session_id": session_id}).sort("created_at", 1):
        out.append({"role": m["role"], "content": m["content"], "created_at": m["created_at"]})
    return out

# ── EVALUATIONS & LEADERBOARD ────────────────────────────────────
@api.post("/evaluations")
async def create_evaluation(data: EvaluationCreate, request: Request):
    user = await require_role(request, ["admin", "organizer"])
    doc = {"team_id": data.team_id, "hackathon_id": data.hackathon_id, "judge_id": user["_id"], "judge_name": user["name"], "scores": data.scores, "total_score": calc_score(data.scores), "notes": data.notes, "created_at": datetime.now(timezone.utc).isoformat()}
    r = await db.evaluations.insert_one(doc)
    doc.pop("_id", None)
    return {"id": str(r.inserted_id), **doc}

@api.get("/evaluations/{tid}")
async def get_evaluations(tid: str, request: Request):
    await get_current_user(request)
    out = []
    async for e in db.evaluations.find({"team_id": tid}):
        e["id"] = str(e["_id"]); del e["_id"]; out.append(e)
    return out

@api.get("/leaderboard/{hid}")
async def get_leaderboard(hid: str):
    pipeline = [{"$match": {"hackathon_id": hid}}, {"$group": {"_id": "$team_id", "avg_score": {"$avg": "$total_score"}, "count": {"$sum": 1}}}, {"$sort": {"avg_score": -1}}]
    out = []; rank = 1
    async for e in db.evaluations.aggregate(pipeline):
        team = await db.teams.find_one({"_id": ObjectId(e["_id"])})
        if team:
            out.append({"rank": rank, "team_id": e["_id"], "team_name": team["name"], "avg_score": round(e["avg_score"], 2), "count": e["count"]}); rank += 1
    return out

# ── VIDEO VIVA PIPELINE ──────────────────────────────────────────
@api.post("/ai/video-viva/upload")
async def upload_video_viva(request: Request, file: UploadFile = File(...)):
    """Upload a hackathon explanation video, run pipeline, return questions."""
    user = await get_current_user(request)
    if not file.filename:
        raise HTTPException(400, "No video file selected")
    content = await file.read()
    if not content:
        raise HTTPException(400, "Uploaded video file is empty")
    if len(content) > 200 * 1024 * 1024:
        raise HTTPException(400, "Video file too large (max 200 MB)")
    try:
        result = await video_pipeline.process_video(content, file.filename, file.content_type)
    except Exception as exc:
        logger.error(f"Video pipeline error: {exc}")
        raise HTTPException(500, f"Video processing failed: {exc}")
    session_id = result["session_id"]
    await db.video_viva_sessions.insert_one({
        "session_id": session_id, "user_id": user["_id"], "filename": file.filename,
        "summary": result["summary"], "transcript": result["transcript"],
        "questions": result["questions"], "answers": [], "status": "questions_generated",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"session_id": session_id, "questions": result["questions"], "summary": result["summary"], "transcript": result["transcript"]}

@api.get("/ai/video-viva/questions/{session_id}")
async def get_video_viva_questions(session_id: str, request: Request):
    """Fetch generated questions for a video viva session."""
    await get_current_user(request)
    doc = await db.video_viva_sessions.find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(404, "Video viva session not found")
    return {"session_id": doc["session_id"], "questions": doc["questions"], "summary": doc.get("summary", ""), "transcript": doc.get("transcript", ""), "answers": doc.get("answers", []), "status": doc.get("status", "unknown")}

@api.post("/ai/video-viva/answer")
async def submit_video_viva_answer(request: Request):
    """Submit an answer for a video viva question and get AI evaluation."""
    user = await get_current_user(request)
    body = await request.json()
    session_id = body.get("session_id", "")
    question_id = body.get("question_id", "")
    answer = body.get("answer", "")
    if not session_id or not question_id or not answer.strip():
        raise HTTPException(400, "session_id, question_id, and answer are required")
    doc = await db.video_viva_sessions.find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(404, "Session not found")
    question = next((q for q in doc["questions"] if q.get("id") == question_id), None)
    if not question:
        raise HTTPException(404, "Question not found in session")
    video_context = {"summary": doc.get("summary", ""), "transcript": doc.get("transcript", "")}
    evaluation = await gemini_client.evaluate_viva_answer(question, answer, video_context)
    answer_doc = {"question_id": question_id, "answer": answer, "evaluation": evaluation, "submitted_at": datetime.now(timezone.utc).isoformat()}
    await db.video_viva_sessions.update_one({"session_id": session_id}, {"$push": {"answers": answer_doc}})
    updated = await db.video_viva_sessions.find_one({"session_id": session_id})
    all_answered = len(updated.get("answers", [])) >= len(updated.get("questions", []))
    if all_answered:
        await db.video_viva_sessions.update_one({"session_id": session_id}, {"$set": {"status": "completed"}})
    return {**evaluation, "completed": all_answered, "answers_count": len(updated.get("answers", [])), "total_questions": len(updated.get("questions", []))}

# ── PDF REPORTS ──────────────────────────────────────────────────
from starlette.responses import StreamingResponse

@api.get("/report/participant/{user_id}")
async def participant_report(user_id: str, request: Request):
    """Generate and download a PDF report for a participant."""
    caller = await get_current_user(request)
    # Allow participants to download their own report, or organizers to download any
    if caller["_id"] != user_id and caller.get("role") not in ("organizer", "admin"):
        raise HTTPException(403, "You can only download your own report")

    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)

    # Find the team
    team = None
    async for t in db.teams.find():
        members = t.get("members", [])
        if any(m.get("user_id") == user_id for m in members):
            t["id"] = str(t["_id"]); del t["_id"]
            team = t
            break

    # Viva sessions for this team
    viva_sessions = []
    if team:
        async for s in db.viva_sessions.find({"team_id": team["id"]}).sort("created_at", -1):
            s["id"] = str(s["_id"]); del s["_id"]
            viva_sessions.append(s)

    # Project info
    project_info = None
    if team:
        project_info = await db.project_info.find_one({"team_id": team["id"]})
        if project_info:
            project_info.pop("_id", None)

    # Plagiarism report
    plagiarism_rpt = None
    if team:
        plagiarism_rpt = await db.plagiarism_reports.find_one({"team_id": team["id"]})
        if plagiarism_rpt:
            plagiarism_rpt.pop("_id", None)

    pdf_bytes = report_generator.generate_participant_report(user, team or {}, viva_sessions, project_info, plagiarism_rpt)
    safe_name = (user.get("name", "participant") or "participant").replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'}
    )

@api.get("/report/hackathon/{hackathon_id}")
async def hackathon_report(hackathon_id: str, request: Request):
    """Generate and download a full hackathon PDF report (organizer-only)."""
    user = await get_current_user(request)
    if user.get("role") not in ("organizer", "admin"):
        raise HTTPException(403, "Only organizers can download hackathon reports")

    hackathon = await db.hackathons.find_one({"_id": ObjectId(hackathon_id)})
    if not hackathon:
        raise HTTPException(404, "Hackathon not found")
    hackathon["id"] = str(hackathon["_id"]); del hackathon["_id"]

    # All teams in this hackathon
    teams_data = []
    all_team_ids = []
    async for t in db.teams.find({"hackathon_id": hackathon_id}):
        t["id"] = str(t["_id"]); del t["_id"]
        all_team_ids.append(t["id"])
        proj = await db.project_info.find_one({"team_id": t["id"]})
        if proj: proj.pop("_id", None)
        teams_data.append({"team": t, "members": t.get("members", []), "project_info": proj})

    # Leaderboard
    pipeline = [{"$match": {"hackathon_id": hackathon_id}}, {"$group": {"_id": "$team_id", "avg_score": {"$avg": "$total_score"}, "count": {"$sum": 1}}}, {"$sort": {"avg_score": -1}}]
    leaderboard = []; rank = 1
    async for e in db.evaluations.aggregate(pipeline):
        team = await db.teams.find_one({"_id": ObjectId(e["_id"])})
        if team:
            leaderboard.append({"rank": rank, "team_id": e["_id"], "team_name": team["name"], "avg_score": round(e["avg_score"], 2), "count": e["count"]}); rank += 1

    # Plagiarism reports
    plagiarism_reports = {}
    async for r in db.plagiarism_reports.find({"team_id": {"$in": all_team_ids}}):
        r.pop("_id", None)
        plagiarism_reports[r["team_id"]] = r

    # Viva data
    viva_data = {}
    for tid in all_team_ids:
        sessions = []
        async for s in db.viva_sessions.find({"team_id": tid}):
            s.pop("_id", None)
            sessions.append(s)
        viva_data[tid] = sessions

    pdf_bytes = report_generator.generate_hackathon_report(hackathon, teams_data, leaderboard, plagiarism_reports, viva_data)
    safe_name = (hackathon.get("name", "hackathon") or "hackathon").replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'}
    )

# ── EXTENSION & TELEMETRY ────────────────────────────────────────
class TelemetryData(BaseModel):
    team_id: str
    extension_key: str
    event_type: str
    details: Dict[str, Any]

class ExtensionLinkRequest(BaseModel):
    team_name: str

@api.post("/extension/link")
async def link_extension(data: ExtensionLinkRequest):
    team = await db.teams.find_one({"name": {"$regex": f"^{data.team_name}$", "$options": "i"}})
    if not team:
        raise HTTPException(404, "Team not found")
    
    if "extension_key" not in team:
        ext_key = str(uuid.uuid4())
        await db.teams.update_one({"_id": team["_id"]}, {"$set": {"extension_key": ext_key}})
        team["extension_key"] = ext_key

    return {"team_id": str(team["_id"]), "team_name": team["name"], "extension_key": team["extension_key"]}

@api.post("/extension/telemetry")
async def receive_telemetry(data: TelemetryData):
    team = await db.teams.find_one({"_id": ObjectId(data.team_id), "extension_key": data.extension_key})
    if not team:
        raise HTTPException(401, "Invalid team or extension key")
    
    log_doc = {
        "team_id": data.team_id,
        "event_type": data.event_type,
        "details": data.details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await db.telemetry_logs.insert_one(log_doc)
    return {"message": "Telemetry received"}

@api.get("/extension/telemetry/{tid}")
async def get_team_telemetry(tid: str, request: Request):
    await get_current_user(request)
    out = []
    async for log in db.telemetry_logs.find({"team_id": tid}).sort("timestamp", -1):
        log["id"] = str(log["_id"])
        del log["_id"]
        out.append(log)
    return out

# ── STATS ────────────────────────────────────────────────────────
@api.get("/stats/dashboard")
async def dashboard_stats(request: Request):
    await get_current_user(request)
    return {"hackathons": await db.hackathons.count_documents({}), "teams": await db.teams.count_documents({}), "users": await db.users.count_documents({}), "evaluations": await db.evaluations.count_documents({})}

@api.get("/")
async def root():
    return {"message": "AI Judge v2 API", "version": "2.0.0"}

app.include_router(api)
