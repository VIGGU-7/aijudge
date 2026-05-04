import asyncio
import bcrypt
import random
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "aijudge_v2")

async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("Clearing existing data...")
    await db.users.delete_many({})
    await db.hackathons.delete_many({})
    await db.teams.delete_many({})
    await db.project_info.delete_many({})
    await db.viva_sessions.delete_many({})
    await db.evaluations.delete_many({})
    await db.plagiarism_reports.delete_many({})
    await db.telemetry_logs.delete_many({})

    print("Creating Organizer...")
    org_pw = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    org_res = await db.users.insert_one({
        "name": "Alice Organizer",
        "email": "organizer@example.com",
        "password_hash": org_pw,
        "role": "organizer",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    org_id = str(org_res.inserted_id)

    print("Creating Hackathons...")
    hackathons = [
        {"name": "Global AI Hackathon 2026", "desc": "Build the future of AI in 48 hours.", "status": "active", "offset": 0},
        {"name": "Web3 Innovators Sprint", "desc": "Decentralizing the web, one block at a time.", "status": "completed", "offset": -30},
        {"name": "FinTech Disruption Challenge", "desc": "Redefining banking and finance.", "status": "completed", "offset": -60},
        {"name": "HealthTech Solutions", "desc": "Improving lives through technology.", "status": "draft", "offset": 15},
    ]
    
    hackathon_ids = []
    for h in hackathons:
        res = await db.hackathons.insert_one({
            "name": h["name"],
            "description": h["desc"],
            "start_date": (datetime.now(timezone.utc) + timedelta(days=h["offset"]-2)).isoformat(),
            "end_date": (datetime.now(timezone.utc) + timedelta(days=h["offset"])).isoformat(),
            "status": h["status"],
            "organizer_id": org_id,
            "created_at": (datetime.now(timezone.utc) + timedelta(days=h["offset"]-10)).isoformat()
        })
        hackathon_ids.append(str(res.inserted_id))

    active_hack_id = hackathon_ids[0]

    print("Creating Participants and Teams...")
    teams_data = [
        {"name": "Neural Ninjas", "email": "participant@example.com", "user": "Bob Hacker", "repo": "neural-ninjas"},
        {"name": "Cyber Syndicate", "email": "cyber@example.com", "user": "Eve Smith", "repo": "cyber-syndicate"},
        {"name": "Data Drifters", "email": "data@example.com", "user": "Charlie Tech", "repo": "data-drifters"},
        {"name": "Quantum Quails", "email": "quantum@example.com", "user": "Dave Dev", "repo": "quantum-quails"},
        {"name": "Syntax Squad", "email": "syntax@example.com", "user": "Grace Hopper", "repo": "syntax-squad"}
    ]

    for i, t_data in enumerate(teams_data):
        # Create user
        pw = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_res = await db.users.insert_one({
            "name": t_data["user"],
            "email": t_data["email"],
            "password_hash": pw,
            "role": "participant",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        user_id = str(user_res.inserted_id)

        # Create team
        ext_key = f"ext-key-{t_data['repo']}"
        team_res = await db.teams.insert_one({
            "name": t_data["name"],
            "hackathon_id": active_hack_id,
            "github_repo": f"https://github.com/example/{t_data['repo']}",
            "members": [{"user_id": user_id, "name": t_data["user"]}],
            "extension_key": ext_key,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        team_id = str(team_res.inserted_id)

        # Create Telemetry Logs for Neural Ninjas (Malpractice)
        if t_data["name"] == "Neural Ninjas":
            await db.telemetry_logs.insert_many([
                {
                    "team_id": team_id,
                    "event_type": "malpractice_detected",
                    "details": {"reason": "Massive copy-paste detected", "lines_pasted": 450, "file": "backend/auth.py"},
                    "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=120)).isoformat()
                },
                {
                    "team_id": team_id,
                    "event_type": "malpractice_detected",
                    "details": {"reason": "Focus lost for extended period during active coding", "duration_minutes": 45},
                    "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
                },
                {
                    "team_id": team_id,
                    "event_type": "telemetry_ping",
                    "details": {"status": "active", "loc_written": 12},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            ])

        # Create project info
        await db.project_info.insert_one({
            "team_id": team_id,
            "github_url": f"https://github.com/example/{t_data['repo']}",
            "tech_stack": ["React", "FastAPI", "MongoDB"] if i % 2 == 0 else ["Vue", "Node.js", "PostgreSQL"],
            "features": ["Feature A", "Feature B", "Feature C"],
            "architecture_description": "Standard modern web architecture.",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Create Plagiarism Report (make one of them flagged)
        score = 85 if i == 1 else random.randint(5, 20)
        risk = "red" if score > 50 else "green"
        await db.plagiarism_reports.insert_one({
            "team_id": team_id,
            "overall_score": score,
            "risk_level": risk,
            "summary": f"Plagiarism score is {score}%.",
            "file_results": [
                {"file": "main.py", "plagiarism_score": score, "analysis": "Analysis result here."}
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Create Viva Session
        viva_score = random.randint(60, 95)
        await db.viva_sessions.insert_one({
            "team_id": team_id,
            "user_id": user_id,
            "summary": {"overall_score": viva_score, "understanding_level": "good"},
            "questions": [
                {
                    "question": "Can you explain your database choice?",
                    "category": "architecture",
                    "answer": "We chose it for scalability.",
                    "evaluation": {
                        "score": viva_score,
                        "feedback": "Good answer.",
                        "understanding_level": "good"
                    }
                }
            ],
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        # Create Evaluation
        await db.evaluations.insert_one({
            "team_id": team_id,
            "hackathon_id": active_hack_id,
            "evaluator_id": org_id,
            "criteria_scores": {"innovation": random.randint(5,10), "execution": random.randint(5,10), "presentation": random.randint(5,10)},
            "total_score": random.randint(65, 95),
            "feedback": "Solid effort.",
            "created_at": datetime.now(timezone.utc).isoformat()
        })

    print("✅ Database Seeded Successfully with Expanded Mock Data!")
    print("-" * 40)
    print("🚀 MOCK ACCOUNTS CREATED")
    print("-" * 40)
    print("Role: ORGANIZER")
    print("Email: organizer@example.com")
    print("Password: password123")
    print("-" * 40)
    print("Role: PRIMARY PARTICIPANT")
    print("Email: participant@example.com")
    print("Password: password123")
    print("-" * 40)

if __name__ == "__main__":
    asyncio.run(seed())
