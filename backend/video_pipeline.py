"""
Video Pipeline for AI Judge — Server-side adapter.
Adapts the concepts from video/pipeline_video_to_llm.py for the FastAPI backend
using Gemini's native video understanding.

Pipeline: upload video → Gemini analyzes → generates 5 structured viva questions.
"""

import os
import time
import json
import uuid
import asyncio
import tempfile
import google.generativeai as genai


def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


async def process_video(video_bytes: bytes, filename: str, mime_type=None):
    """Full pipeline: video bytes -> summary -> structured questions."""

    def _run():
        model = _get_model()
        suffix = os.path.splitext(filename or "video.mp4")[1] or ".mp4"
        if not mime_type:
            mime_map = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".avi": "video/x-msvideo"}
            effective_mime = mime_map.get(suffix.lower(), "video/mp4")
        else:
            effective_mime = mime_type

        temp_path = None
        uploaded_file = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_bytes)
                temp_path = tmp.name

            uploaded_file = genai.upload_file(temp_path, mime_type=effective_mime, display_name=filename or "hackathon_video")

            # Wait for file to become active
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(5)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise Exception("Gemini failed to process the video file.")

            # Step 1: Generate summary + transcript
            summary_response = model.generate_content([
                "Watch this entire video carefully. This is a hackathon team explaining their project.\n\n"
                "Provide:\n1. **TRANSCRIPT**: Verbatim transcript of everything spoken.\n"
                "2. **SUMMARY**: Detailed chronological breakdown of visual events, code shown, slides, demos.\n\n"
                "Format:\n## TRANSCRIPT\n<transcript>\n\n## SUMMARY\n<summary>",
                uploaded_file,
            ])
            full_analysis = (summary_response.text or "").strip()

            transcript = ""
            summary = full_analysis
            if "## TRANSCRIPT" in full_analysis and "## SUMMARY" in full_analysis:
                parts = full_analysis.split("## SUMMARY")
                transcript = parts[0].replace("## TRANSCRIPT", "").strip()
                summary = parts[1].strip() if len(parts) > 1 else full_analysis

            # Step 2: Generate structured questions
            questions_response = model.generate_content(
                "You are a strict hackathon judge. Based on this video analysis, generate exactly 5 "
                "challenging viva questions.\n\n"
                f"VIDEO ANALYSIS:\n{full_analysis}\n\n"
                "Return a JSON array with 5 objects each having:\n"
                '{"question":"...","category":"code_deep_dive|feature_probe|tech_stack|architecture|ppt_verification",'
                '"difficulty":"medium|hard","topic":"...","reference":"..."}\n\n'
                "Return ONLY the JSON array."
            )
            raw = (questions_response.text or "").strip()
            questions = _parse_questions(raw)
            for q in questions:
                q["id"] = str(uuid.uuid4())

            return {"session_id": str(uuid.uuid4()), "summary": summary, "transcript": transcript, "questions": questions}
        finally:
            if uploaded_file:
                try: genai.delete_file(uploaded_file.name)
                except: pass
            if temp_path and os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass

    return await asyncio.to_thread(_run)


def _parse_questions(raw_text):
    t = raw_text.strip()
    if t.startswith("```json"): t = t[7:]
    if t.startswith("```"): t = t[3:]
    if t.endswith("```"): t = t[:-3]
    t = t.strip()
    try:
        parsed = json.loads(t)
        if isinstance(parsed, list): return parsed
        if isinstance(parsed, dict) and "questions" in parsed: return parsed["questions"]
        return [parsed]
    except json.JSONDecodeError:
        return [{"question": t[:500] or "Could not parse questions.", "category": "general", "difficulty": "medium", "topic": "video", "reference": "uploaded video"}]
