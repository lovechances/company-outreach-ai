from app.llm import call_llm


def write_outreach(analysis: dict, source_url: str) -> dict:
    prompt = f"""
    You are an outreach strategist.

    Using the business analysis below, write:

    1. a short lead brief
    2. a cold email opener
    3. a DM opener
    4. one audit angle
    5. one offer hook

    Rules:
    - be specific, not flattering
    - avoid fake compliments
    - point out one real likely weakness or missed opportunity
    - make the outreach sound practical and commercially useful
    - keep it concise
    - do not sound like generic AI marketing copy

    Source URL:
    {source_url}

    Analysis:
    {analysis}
    """.strip()

    output = call_llm(prompt)

    return {
        "tool": "writer",
        "status": "ok",
        "message": "Outreach assets generated.",
        "data": {
            "output": output
        },
    }