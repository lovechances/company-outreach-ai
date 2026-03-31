from app.site_collector import collect_site
from app.business_analyzer import analyze_business
from app.outreach_writer import write_outreach
from app.final_formatter import format_final_report


def run_lead_brief_operator(url: str) -> dict:
    collector_result = collect_site(url)

    if collector_result["status"] != "ok":
        return {
            "tool": "operator",
            "status": "failed",
            "message": collector_result["message"],
            "data": {
                "collector": collector_result,
                "analyzer": None,
                "writer": None,
            },
        }

    combined_text = collector_result["data"]["combined_text"]

    analyzer_result = analyze_business(combined_text, url)

    if analyzer_result["status"] != "ok":
        return {
            "tool": "operator",
            "status": "failed",
            "message": analyzer_result["message"],
            "data": {
                "collector": collector_result,
                "analyzer": analyzer_result,
                "writer": None,
            },
        }

    writer_result = write_outreach(analyzer_result["data"], url)

    formatter_result = format_final_report(url, collector_result, analyzer_result, writer_result)

    return {
        "tool": "operator",
        "status": "ok",
        "message": "Lead brief operator completed.",
        "data": {
            "collector": collector_result,
            "analyzer": analyzer_result,
            "writer": writer_result,
            "formatter": formatter_result,
        },
    }