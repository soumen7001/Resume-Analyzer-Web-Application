"""
Google AI Studio Analyzer Module
Uses Google Gemini via google-generativeai SDK to perform
deep, AI-powered resume analysis.

Analysis dimensions:
  1. Overall quality & ATS score (0-100)
  2. Grammar & spelling corrections
  3. Clarity & readability improvements
  4. Action verb enhancement suggestions
  5. Quantified achievements evaluation
  6. Structure & formatting feedback
  7. Job description alignment (if JD provided)
  8. Prioritized improvement action items
"""

import os
import json
import re
import textwrap
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = os.environ.get(
    "GOOGLE_API_KEY",
     ""
)
GOOGLE_MODEL = os.environ.get("GOOGLE_AI_MODEL", "gemini-2.5-flash")

# ---------------------------------------------------------------------------
# Lazy import — only required when AI analysis is requested
# ---------------------------------------------------------------------------
_genai = None


def _get_genai():
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            _genai = genai
        except ImportError:
            raise RuntimeError(
                "google-generativeai package is required for AI analysis. "
                "Install it with: pip install google-generativeai"
            )
    return _genai


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _build_prompt(parsed_resume: Dict[str, Any], job_description: str = "") -> str:
    resume_text = parsed_resume.get("raw_text", "")
    skills = parsed_resume.get("skills", {})
    contact = parsed_resume.get("contact_info", {})

    tech_skills = skills.get("technical", [])
    soft_skills = skills.get("soft", [])
    education = parsed_resume.get("education", [])
    experience = parsed_resume.get("experience", [])
    projects = parsed_resume.get("projects", [])
    certifications = parsed_resume.get("certifications", [])

    jd_section = ""
    if job_description and job_description.strip():
        jd_section = f"""
---
JOB DESCRIPTION:
{job_description.strip()}
---
Please also include a 'jd_alignment' section in your JSON response with:
- 'match_score' (0-100): how well the resume aligns with the JD
- 'matching_points': list of JD requirements already met
- 'missing_points': list of JD requirements not covered
- 'keyword_suggestions': list of important JD keywords to add
"""

    prompt = textwrap.dedent(f"""
You are an expert career coach and ATS (Applicant Tracking System) specialist.

Analyze the resume below thoroughly and return ONLY a valid JSON object
(no markdown fences, no extra prose) with these exact keys:

{{
  "overall_score": <0-100 integer>,
  "ats_score": <0-100 integer>,
  "grammar_corrections": [
    {{"original": "<text>", "corrected": "<corrected text>", "reason": "<brief reason>"}}
  ],
  "clarity_improvements": [
    {{"original": "<text>", "improved": "<improved text>", "reason": "<brief reason>"}}
  ],
  "action_verb_suggestions": [
    {{"original_phrase": "<weak phrase>", "suggested_phrase": "<stronger action verb phrase>"}}
  ],
  "quantified_achievements_feedback": "<paragraph evaluating use of numbers/metrics>",
  "structure_feedback": [
    "<bullet point about structure/formatting>"
  ],
  "strengths": [
    "<bullet point strength>"
  ],
  "improvements": [
    "<prioritized bullet point improvement>"
  ],
  "recommendations": [
    "<actionable recommendation>"
  ]
}}
{jd_section}
---
RESUME RAW TEXT:
{resume_text}

DETECTED TECHNICAL SKILLS: {", ".join(tech_skills)}
DETECTED SOFT SKILLS: {", ".join(soft_skills)}
EDUCATION ENTRIES: {len(education)}
EXPERIENCE ENTRIES: {len(experience)}
PROJECTS: {len(projects)}
CERTIFICATIONS: {len(certifications)}
CONTACT INFO: email={contact.get('email', 'N/A')}, phone={contact.get('phone', 'N/A')}, linkedin={contact.get('linkedin', 'N/A')}, github={contact.get('github', 'N/A')}

Rules:
- Be honest and constructive — do not inflate scores.
- Provide at least 3 grammar corrections if issues exist, otherwise empty list.
- Provide at least 3 clarity improvements if issues exist, otherwise empty list.
- Provide at least 3 action verb suggestions.
- Scores should reflect real ATS compatibility.
- Return ONLY the JSON object. No markdown, no code fences, no preamble.
""").strip()

    return prompt


def _parse_ai_response(raw_text: str) -> Dict[str, Any]:
    """Extract JSON from AI response, handling markdown fences gracefully."""
    if not raw_text:
        return {}

    text = raw_text.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # Try to find the first {...} block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": raw_text, "_parse_error": True}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ai_analyze_resume(
    parsed_resume: Dict[str, Any],
    job_description: str = "",
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Run AI-powered resume analysis via Google Gemini.

    Args:
        parsed_resume: Parsed resume data from resume_parser.parse_resume()
        job_description: Optional job description text
        timeout: Request timeout in seconds (passed to the SDK if supported)

    Returns:
        Dictionary with AI analysis results. Falls back to an error dict
        if the API call fails.
    """
    try:
        genai = _get_genai()
    except RuntimeError as exc:
        return {
            "error": str(exc),
            "ai_enabled": False,
            "fallback": "Install google-generativeai to enable AI analysis.",
        }

    prompt = _build_prompt(parsed_resume, job_description)

    try:
        model = genai.GenerativeModel(GOOGLE_MODEL)
        generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.9,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        raw = response.text or ""

        ai_result = _parse_ai_response(raw)

        # Attach metadata
        ai_result.setdefault("ai_enabled", True)
        ai_result.setdefault("model", GOOGLE_MODEL)
        ai_result.setdefault("provider", "Google AI Studio")

        return ai_result

    except Exception as exc:
        return {
            "error": f"Google AI analysis failed: {str(exc)}",
            "ai_enabled": False,
            "provider": "Google AI Studio",
        }


def merge_ai_with_traditional(
    traditional: Dict[str, Any],
    ai: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Merge AI analysis results into the traditional analysis result dict
    so the frontend can render both side by side.

    Args:
        traditional: Result from analyzer.analyze_resume()
        ai: Result from ai_analyze_resume()

    Returns:
        Merged dictionary with both sets of results.
    """
    merged = dict(traditional)

    # AI-specific top-level keys
    ai_keys = [
        "overall_score",
        "ats_score",
        "grammar_corrections",
        "clarity_improvements",
        "action_verb_suggestions",
        "quantified_achievements_feedback",
        "structure_feedback",
        "strengths",
        "improvements",
        "recommendations",
        "jd_alignment",
    ]

    for key in ai_keys:
        if key in ai:
            merged[f"ai_{key}"] = ai[key]

    merged["ai_enabled"] = ai.get("ai_enabled", False)
    merged["ai_provider"] = ai.get("provider", "Google AI Studio")
    merged["ai_model"] = ai.get("model", GOOGLE_MODEL)

    if "error" in ai:
        merged["ai_error"] = ai["error"]

    return merged


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample = {
        "raw_text": (
            "John Doe\n"
            "john.doe@email.com | (555) 123-4567\n\n"
            "EXPERIENCE\n"
            "Software Engineer at TechCorp — worked on Python and Django projects\n"
            "Junior Developer at StartupXYZ — helped with React and APIs\n\n"
            "SKILLS\n"
            "Python, JavaScript, React, Django, Docker, AWS\n\n"
            "EDUCATION\n"
            "BS Computer Science, State University, 2020\n"
        ),
        "skills": {
            "technical": ["Python", "JavaScript", "React", "Django", "Docker", "AWS"],
            "soft": ["Communication", "Teamwork"],
        },
        "contact_info": {
            "email": "john.doe@email.com",
            "phone": "(555) 123-4567",
            "linkedin": "johndoe",
            "github": "johndoe",
        },
        "education": [{"raw": "BS Computer Science"}],
        "experience": [
            {"raw": "Software Engineer at TechCorp"},
            {"raw": "Junior Developer at StartupXYZ"},
        ],
        "projects": [],
        "certifications": [],
        "word_count": 52,
        "char_count": 320,
    }

    jd = (
        "We are seeking a Senior Python Developer with 5+ years of experience in Django, "
        "REST APIs, PostgreSQL, Docker, and AWS. Experience with CI/CD pipelines and "
        "Agile methodologies is a plus."
    )

    print("Running Google AI Studio resume analysis...")
    result = ai_analyze_resume(sample, jd)
    print(json.dumps(result, indent=2))
