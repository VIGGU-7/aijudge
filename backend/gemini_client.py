"""
Gemini 2.5 Flash client for AI Judge v2.
Handles all AI operations: question generation, answer evaluation, code analysis, etc.
"""
import os
import json
import asyncio
import tempfile
import google.generativeai as genai
from typing import Optional


def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


async def _generate(prompt: str) -> str:
    """Run model.generate_content in a thread to avoid blocking the event loop."""
    model = _get_model()
    response = await asyncio.to_thread(model.generate_content, prompt)
    return response.text


async def transcribe_audio(audio_bytes: bytes, filename: str, mime_type: Optional[str] = None) -> str:
    """Transcribe recorded audio using Gemini's file upload flow."""

    # Skip very short audio (likely silence or noise)
    if len(audio_bytes) < 1000:
        return ""

    def _run() -> str:
        model = _get_model()
        suffix = os.path.splitext(filename or "recording.webm")[1] or ".webm"
        temp_path = None
        uploaded = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            uploaded = genai.upload_file(
                temp_path,
                mime_type=mime_type or "audio/webm",
                display_name=filename or "recording.webm",
            )
            response = model.generate_content(
                [
                    "Listen to this audio recording carefully. "
                    "If you hear clear human speech, transcribe ONLY the exact words spoken. "
                    "Do NOT add any commentary, labels, or formatting. "
                    "If the audio is silent, contains only background noise, music, or no clear human speech, "
                    "respond with exactly the single word: SILENCE\n"
                    "Return ONLY the transcript or SILENCE, nothing else.",
                    uploaded,
                ]
            )
            text = (response.text or "").strip()
            # Filter out hallucinated/empty responses
            if not text or text == "SILENCE" or len(text) < 3:
                return ""
            # Filter out common hallucination patterns
            hallucination_markers = [
                "constitution", "amendment", "emergency broadcast",
                "no speech", "no audio", "no clear", "background noise",
                "silence detected", "inaudible", "[silence]", "[noise]",
                "cannot transcribe", "no human speech",
            ]
            text_lower = text.lower()
            if any(marker in text_lower for marker in hallucination_markers):
                return ""
            return text
        finally:
            if uploaded is not None:
                try:
                    genai.delete_file(uploaded.name)
                except Exception:
                    pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    return await asyncio.to_thread(_run)



def _safe_json(text: str) -> dict:
    """Parse JSON from Gemini response, stripping markdown wrappers."""
    t = text.strip()
    if t.startswith("```json"):
        t = t[7:]
    if t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    t = t.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return {"raw_text": text}


async def analyze_codebase(repo_data: dict) -> dict:
    """Analyze a codebase to understand tech stack, patterns, and structure."""
    file_tree = repo_data.get("file_tree", "")
    key_files = repo_data.get("key_files", [])
    readme = repo_data.get("readme", "")

    files_context = ""
    for f in key_files[:15]:
        content = f.get("content", "")[:3000]
        files_context += f"\n--- {f['path']} ---\n{content}\n"

    prompt = f"""You are an expert code analyst. Analyze this codebase and return a JSON report.

FILE TREE:
{file_tree[:3000]}

README:
{readme[:2000]}

KEY SOURCE FILES:
{files_context}

Return a JSON object with:
{{
  "tech_stack": ["list of technologies detected"],
  "frameworks": ["list of frameworks used"],
  "languages": ["programming languages used"],
  "code_patterns": ["architectural patterns found, e.g. MVC, REST, etc."],
  "key_components": ["list of major components/modules"],
  "complexity_assessment": "low/medium/high",
  "notable_implementations": ["interesting or complex implementations found"],
  "potential_concerns": ["any code quality issues, security risks, etc."],
  "summary": "2-3 sentence summary of the project"
}}

Return ONLY valid JSON, no markdown."""

    return _safe_json(await _generate(prompt))


async def analyze_presentation(ppt_data: dict) -> dict:
    """Analyze PPT/PDF content to extract features, architecture, and claims."""

    slides_text = ppt_data.get("full_text", "")

    prompt = f"""You are analyzing a hackathon team's presentation. Extract key information.

PRESENTATION CONTENT:
{slides_text[:8000]}

Return a JSON object with:
{{
  "project_name": "name of the project",
  "problem_statement": "the problem they're solving",
  "solution_description": "their proposed solution",
  "claimed_features": ["list of features they claim to have built"],
  "architecture_description": "their system architecture",
  "tech_stack_mentioned": ["technologies mentioned in the presentation"],
  "team_roles": ["roles mentioned if any"],
  "unique_selling_points": ["what makes their project special"],
  "demo_claims": ["specific demos or functionality they claim to show"],
  "summary": "2-3 sentence summary of the presentation"
}}

Return ONLY valid JSON, no markdown."""

    return _safe_json(await _generate(prompt))


async def build_context_profile(
    repo_data: Optional[dict],
    ppt_data: Optional[dict],
    user_input: dict,
    code_analysis: Optional[dict] = None,
    ppt_analysis: Optional[dict] = None,
) -> dict:
    """Build a comprehensive context profile combining all sources."""

    context_parts = []

    if code_analysis:
        context_parts.append(f"CODE ANALYSIS:\n{json.dumps(code_analysis, indent=2)}")
    if ppt_analysis:
        context_parts.append(f"PPT ANALYSIS:\n{json.dumps(ppt_analysis, indent=2)}")
    if user_input:
        context_parts.append(f"USER DECLARED INFO:\n{json.dumps(user_input, indent=2)}")

    combined = "\n\n".join(context_parts)

    prompt = f"""You are building a comprehensive context profile for a hackathon team evaluation.
Cross-reference all the data sources below and identify matches and discrepancies.

{combined}

Return a JSON object with:
{{
  "code_vs_claims_match": 0-100,
  "detected_but_not_claimed": ["features found in code but not mentioned in PPT"],
  "claimed_but_not_found": ["features claimed in PPT but not found in code"],
  "tech_stack_verified": ["tech actually used based on code"],
  "complexity_assessment": "low/medium/high",
  "authenticity_score": 0-100,
  "key_areas_to_question": ["specific areas that need verification during viva"],
  "summary": "overall assessment of the project"
}}

Return ONLY valid JSON, no markdown."""

    return _safe_json(await _generate(prompt))


async def generate_viva_question(
    context_profile: dict, category: str, previous_questions: list = None
) -> dict:
    """Generate a targeted viva question based on context and category."""

    prev_q = ""
    if previous_questions:
        prev_q = "\n\nPREVIOUS QUESTIONS (do NOT repeat):\n" + "\n".join(
            [f"- {q}" for q in previous_questions[:10]]
        )

    category_prompts = {
        "code_deep_dive": """Generate a question about a SPECIFIC piece of code in their codebase.
Reference actual files, functions, or code patterns you see in the analysis.
The question should test if they actually wrote and understand their code.""",

        "ppt_verification": """Generate a question that VERIFIES a specific claim from their presentation.
Reference something they said in their slides and ask them to prove or explain it in detail.
Focus on claims that might be exaggerated or unverified.""",

        "feature_probe": """Generate a question about a SPECIFIC FEATURE they claim to have built.
Ask them to explain how it works technically, what edge cases they handle, how they tested it.
Pick features that are core to their project.""",

        "tech_stack": """Generate a question about their TECH STACK choice and knowledge.
Ask why they chose specific technologies, how they work, trade-offs, alternatives.
Test if they actually understand the frameworks they used, not just copied boilerplate.""",

        "architecture": """Generate a question about their SYSTEM ARCHITECTURE and design decisions.
Ask about data flow, component interaction, scalability, error handling.
Test their understanding of how the pieces fit together.""",
    }

    category_instruction = category_prompts.get(category, category_prompts["code_deep_dive"])

    ctx_str = json.dumps(context_profile, indent=2)[:6000]

    prompt = f"""You are an AI Judge conducting a hackathon viva examination.

TEAM'S CONTEXT PROFILE:
{ctx_str}

QUESTION CATEGORY: {category}

{category_instruction}
{prev_q}

Return a JSON object with:
{{
  "question": "the specific, targeted question to ask",
  "category": "{category}",
  "topic": "specific topic area",
  "difficulty": "easy/medium/hard",
  "expected_concepts": ["key concepts a correct answer should cover"],
  "reference": "what part of their project this relates to (file, slide, feature)",
  "follow_up_hint": "a follow-up question if their answer is vague"
}}

Return ONLY valid JSON, no markdown."""

    return _safe_json(await _generate(prompt))


async def evaluate_viva_answer(
    question: dict, answer: str, context_profile: dict
) -> dict:
    """Evaluate a participant's viva answer against their context profile."""

    ctx_str = json.dumps(context_profile, indent=2)[:4000]
    q_str = json.dumps(question, indent=2)

    prompt = f"""You are evaluating a hackathon participant's answer in a viva session.

CONTEXT PROFILE:
{ctx_str}

QUESTION ASKED:
{q_str}

PARTICIPANT'S ANSWER:
{answer}

Evaluate their answer carefully. Consider:
1. Does their answer match what's actually in their code?
2. Do they show genuine understanding or are they bluffing?
3. Do they reference specific implementation details?
4. Are there red flags suggesting they didn't write the code?

Return a JSON object with:
{{
  "score": 0-100,
  "understanding_level": "poor/fair/good/excellent",
  "feedback": "detailed feedback on their answer",
  "strengths": ["what they got right"],
  "weaknesses": ["what was missing or wrong"],
  "authenticity_assessment": "genuine/uncertain/suspicious",
  "follow_up_recommended": true/false,
  "follow_up_question": "optional follow-up if needed"
}}

Return ONLY valid JSON, no markdown."""

    return _safe_json(await _generate(prompt))


async def analyze_code_quality(code: str, language: str = "python") -> dict:
    """Analyze code for quality, AI-generation detection, and patterns."""

    prompt = f"""Analyze this {language} code for quality and AI-detection.

```{language}
{code[:5000]}
```

Return JSON:
{{
  "is_ai_generated": true/false,
  "ai_confidence": 0-100,
  "complexity_score": 0-100,
  "quality_score": 0-100,
  "patterns": ["detected patterns"],
  "suggestions": ["improvement suggestions"],
  "summary": "brief analysis"
}}

Return ONLY valid JSON."""

    return _safe_json(await _generate(prompt))


async def check_plagiarism(code: str) -> dict:
    """Check code for plagiarism patterns."""

    prompt = f"""Analyze this code for plagiarism indicators.

```
{code[:5000]}
```

Return JSON:
{{
  "originality_score": 0-100,
  "similar_patterns": ["any patterns that look copied"],
  "verdict": "original/suspicious/plagiarized",
  "explanation": "brief explanation"
}}

Return ONLY valid JSON."""

    return _safe_json(await _generate(prompt))


async def mentor_chat(message: str, code_context: Optional[str] = None) -> str:
    """AI mentor chat for participants."""
    prompt = f"""You are a helpful AI mentor for hackathon participants. Help them learn.
Be encouraging but educational. Don't give complete solutions - guide them.

USER MESSAGE: {message}"""

    if code_context:
        prompt += f"\n\nCODE CONTEXT:\n```\n{code_context[:3000]}\n```"

    return await _generate(prompt)


async def analyze_plagiarism(files: dict) -> dict:
    """
    Analyze code files for plagiarism using Gemini.
    Takes a dict of {filename: code_content} and returns per-file and overall scores.
    """
    if not files:
        return {"overall_score": 0, "risk_level": "minimal", "files": []}

    # Build the file list for the prompt (limit to 15 files, 4000 chars each)
    file_entries = []
    for fname, content in list(files.items())[:15]:
        truncated = content[:4000]
        file_entries.append(f"--- FILE: {fname} ---\n{truncated}\n--- END FILE ---")

    files_block = "\n\n".join(file_entries)

    prompt = f"""You are an expert code plagiarism detector for a hackathon judging system.
Analyze each code file below and assess how likely it is to be plagiarized or copied from public sources.

For each file, evaluate:
1. Does it contain large blocks commonly found in tutorials, Stack Overflow, or popular GitHub repos?
2. Is there evidence of copy-paste (inconsistent style, leftover comments from other projects)?
3. Does it look AI-generated (overly generic, boilerplate-heavy, unnaturally perfect)?
4. Is the code original and project-specific?

Return ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "overall_score": <number 0-100, overall plagiarism percentage>,
  "risk_level": "<minimal|low|medium|high>",
  "summary": "<1-2 sentence summary>",
  "files": [
    {{
      "filename": "<exact filename>",
      "plagiarism_score": <number 0-100>,
      "matched_source": "<likely source or 'Original' if clean>",
      "reason": "<brief explanation>"
    }}
  ]
}}

Rules:
- Boilerplate/config files (package.json, .env, etc.) should score low (5-15%) — they are naturally similar across projects
- Framework scaffolding (create-react-app, express boilerplate) should score 10-25%
- Truly original hackathon logic should score 0-10%
- Direct copies from tutorials/repos should score 70-100%
- Be fair and realistic. Hackathon projects naturally use libraries and patterns.

CODE FILES TO ANALYZE:
{files_block}"""

    raw = await _generate(prompt)
    # Clean and parse
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "overall_score": 0,
            "risk_level": "error",
            "summary": "Failed to parse plagiarism analysis",
            "files": []
        }
