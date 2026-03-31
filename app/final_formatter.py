def format_final_report(source_url: str, collector_result: dict, analyzer_result: dict, writer_result: dict) -> dict:
    collector_data = collector_result.get("data", {})
    analyzer_data = analyzer_result.get("data", {})
    writer_output = writer_result.get("data", {}).get("output", "")

    collection_status = collector_data.get("collection_status", "unknown")
    word_count = collector_data.get("word_count", 0)
    pages = collector_data.get("pages", [])

    company_name = analyzer_data.get("company_name", "Unknown")
    what_they_sell = analyzer_data.get("what_they_sell", "")
    target_customer = analyzer_data.get("target_customer", "")
    business_model_guess = analyzer_data.get("business_model_guess", "")
    positioning = analyzer_data.get("positioning", "")
    short_summary = analyzer_data.get("short_summary", "")

    likely_strengths = analyzer_data.get("likely_strengths", [])
    likely_weaknesses = analyzer_data.get("likely_weaknesses", [])
    likely_growth_opportunities = analyzer_data.get("likely_growth_opportunities", [])

    likely_bottleneck = analyzer_data.get("likely_bottleneck", "")
    messaging_gap = analyzer_data.get("messaging_gap", "")
    conversion_gap = analyzer_data.get("conversion_gap", "")
    best_offer_angle = analyzer_data.get("best_offer_angle", "")

    observed_section = []
    if what_they_sell:
        observed_section.append(f"- Offer: {what_they_sell}")
    if target_customer:
        observed_section.append(f"- Target customer: {target_customer}")
    if business_model_guess:
        observed_section.append(f"- Business model guess: {business_model_guess}")
    if positioning:
        observed_section.append(f"- Positioning: {positioning}")

    inferred_section = []
    if likely_bottleneck:
        inferred_section.append(f"- Likely bottleneck: {likely_bottleneck}")
    if messaging_gap:
        inferred_section.append(f"- Messaging gap: {messaging_gap}")
    if conversion_gap:
        inferred_section.append(f"- Conversion gap: {conversion_gap}")

    strengths_text = "\n".join(f"- {x}" for x in likely_strengths) if likely_strengths else "- None identified"
    weaknesses_text = "\n".join(f"- {x}" for x in likely_weaknesses) if likely_weaknesses else "- None identified"
    opportunities_text = "\n".join(f"- {x}" for x in likely_growth_opportunities) if likely_growth_opportunities else "- None identified"

    observed_text = "\n".join(observed_section) if observed_section else "- No clear observed facts extracted"
    inferred_text = "\n".join(inferred_section) if inferred_section else "- No strong inferred issues extracted"

    page_lines = "\n".join(f"- {page['label']}: {page['url']}" for page in pages) if pages else "- No pages collected"

    recommendation = "Weak target."
    if collection_status in {"full", "partial"} and (best_offer_angle or likely_bottleneck or messaging_gap or conversion_gap):
        recommendation = "Good target for personalized outreach."

    final_output = f"""
=== FINAL LEAD BRIEF ===

Source URL:
{source_url}

Company:
{company_name}

Collection:
- Status: {collection_status}
- Word count: {word_count}
- Pages collected: {len(pages)}

Collected Pages:
{page_lines}

Business Snapshot:
{short_summary or "- No summary generated"}

Observed From Site:
{observed_text}

Likely Strengths:
{strengths_text}

Likely Weaknesses:
{weaknesses_text}

Likely Growth Opportunities:
{opportunities_text}

Inferred Issues / Gaps:
{inferred_text}

Best Offer Angle:
- {best_offer_angle or "No strong offer angle identified"}

Recommendation:
- {recommendation}

=== WRITER OUTPUT ===

{writer_output}
""".strip()

    return {
        "tool": "formatter",
        "status": "ok",
        "message": "Final report formatted.",
        "data": {
            "final_output": final_output
        },
    }