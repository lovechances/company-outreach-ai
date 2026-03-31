import json
from app.llm import call_llm


def analyze_business(collected_text: str, source_url: str) -> dict:
    prompt = f"""
    You are a business website analyst.

    Return ONLY valid JSON.
    THAT IS MOST IMPORTANT. Return ONLY valid JSON. Return ONLY valid JSON. Return ONLY valid JSON.
    Do not include markdown.
    Do not include explanation text.
    Do not wrap in triple backticks.
    Focus on practical business interpretation, not generic summaries.
    If information is incomplete, make the best grounded guess from the available site text.
    Do not invent features that are not implied by the site.

    Use this exact schema:
    {{
    "company_name": "",
    "what_they_sell": "",
    "target_customer": "",
    "business_model_guess": "",
    "positioning": "",
    "likely_strengths": [],
    "likely_weaknesses": [],
    "likely_growth_opportunities": [],
    "likely_bottleneck": "",
    "messaging_gap": "",
    "conversion_gap": "",
    "best_offer_angle": "",
    "short_summary": ""
    }}

    Source URL:
    {source_url}

    Website text:
    {collected_text[:12000]}
    """.strip()

    raw = call_llm(prompt).strip()

    # strip accidental markdown fences if model ignores instructions
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
        return {
            "tool": "analyzer",
            "status": "ok",
            "message": "Business analysis completed.",
            "data": parsed,
        }
    except Exception:
        return {
            "tool": "analyzer",
            "status": "error",
            "message": "Could not parse analysis output.",
            "data": {
                "raw_output": raw
            },
        }