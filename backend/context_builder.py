"""
Builds a comprehensive Context Profile from repo data, PPT data, and user inputs.
The Context Profile is what Gemini uses to generate targeted viva questions.
"""
from typing import Optional
from gemini_client import analyze_codebase, analyze_presentation, build_context_profile as _llm_build


async def build_profile(
    repo_data: Optional[dict],
    ppt_data: Optional[dict],
    user_input: dict,
) -> dict:
    """
    Build a full context profile:
    1. Analyze codebase (if repo data provided)
    2. Analyze presentation (if PPT data provided)
    3. Cross-reference everything with Gemini
    """

    code_analysis = None
    ppt_analysis = None

    # Step 1: Analyze codebase
    if repo_data and not repo_data.get("error"):
        code_analysis = await analyze_codebase(repo_data)

    # Step 2: Analyze presentation
    if ppt_data and ppt_data.get("full_text"):
        ppt_analysis = await analyze_presentation(ppt_data)

    # Step 3: Cross-reference with Gemini
    ai_profile = await _llm_build(
        repo_data=repo_data,
        ppt_data=ppt_data,
        user_input=user_input,
        code_analysis=code_analysis,
        ppt_analysis=ppt_analysis,
    )

    # Build the final profile
    profile = {
        "codebase": {
            "file_tree": repo_data.get("file_tree", "") if repo_data else "",
            "key_files": repo_data.get("key_files", []) if repo_data else [],
            "tech_stack": repo_data.get("tech_stack", []) if repo_data else [],
            "total_files": repo_data.get("total_files", 0) if repo_data else 0,
            "analysis": code_analysis,
        },
        "presentation": {
            "slides": ppt_data.get("slides", []) if ppt_data else [],
            "total_slides": ppt_data.get("total_slides", 0) if ppt_data else 0,
            "analysis": ppt_analysis,
        },
        "user_declared": user_input,
        "ai_analysis": ai_profile,
    }

    return profile
