from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.operator import run_lead_brief_operator

from app.config import settings

from app.logger import get_logger

app = FastAPI(
    title="Company Outreach AI",
    description="Analyze a company website and generate a business brief, positioning summary, and outreach angle.",
    version="1.0.4",
)

logger = get_logger("api")


class AnalyzeRequest(BaseModel):
    url: str = Field(..., description="Company website URL to analyze")
    debug: bool = Field(False, description="Include raw operator internals in the response")


class AnalyzeResponse(BaseModel):
    status: str
    source_url: str
    collection_status: Optional[str] = None
    pages_collected: int = 0
    word_count: int = 0

    company_name: Optional[str] = None
    what_they_sell: Optional[str] = None
    target_customer: Optional[str] = None
    business_model_guess: Optional[str] = None
    positioning: Optional[str] = None
    short_summary: Optional[str] = None

    likely_bottleneck: Optional[str] = None
    messaging_gap: Optional[str] = None
    conversion_gap: Optional[str] = None
    best_offer_angle: Optional[str] = None

    final_output: Optional[str] = None
    error_message: Optional[str] = None

    debug_data: Optional[dict] = None


class AnalyzeAcceptedResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[AnalyzeResponse] = None
    error: Optional[str] = None


def shape_operator_response(url: str, result: dict, debug: bool = False) -> dict:
    data = result.get("data", {})
    collector = data.get("collector")
    analyzer = data.get("analyzer")
    formatter = data.get("formatter")

    # failed collector path
    if not collector or collector.get("status") == "failed":
        collector_data = (collector or {}).get("data", {})
        response = {
            "status": "failed",
            "source_url": url,
            "collection_status": collector_data.get("collection_status"),
            "pages_collected": len(collector_data.get("pages", [])),
            "word_count": collector_data.get("word_count", 0),
            "error_message": (collector or {}).get("message", "Collection failed."),
        }

        if debug:
            response["debug_data"] = result

        return response

    collector_data = collector.get("data", {})
    analyzer_data = analyzer.get("data", {}) if analyzer else {}
    formatter_data = formatter.get("data", {}) if formatter else {}

    response = {
        "status": result.get("status", "ok"),
        "source_url": url,
        "collection_status": collector_data.get("collection_status"),
        "pages_collected": len(collector_data.get("pages", [])),
        "word_count": collector_data.get("word_count", 0),

        "company_name": analyzer_data.get("company_name"),
        "what_they_sell": analyzer_data.get("what_they_sell"),
        "target_customer": analyzer_data.get("target_customer"),
        "business_model_guess": analyzer_data.get("business_model_guess"),
        "positioning": analyzer_data.get("positioning"),
        "short_summary": analyzer_data.get("short_summary"),

        "likely_bottleneck": analyzer_data.get("likely_bottleneck"),
        "messaging_gap": analyzer_data.get("messaging_gap"),
        "conversion_gap": analyzer_data.get("conversion_gap"),
        "best_offer_angle": analyzer_data.get("best_offer_angle"),

        "final_output": formatter_data.get("final_output"),
        "error_message": None,
    }

    if debug:
        response["debug_data"] = result

    return response

@app.get("/")
def root():
    return {
        "service": "Company Outreach AI",
        "status": "online",
        "description": "Analyzes a company website and returns a lead brief, business analysis, and outreach angle.",
        "version": "1.0",
        "docs_url": "/docs",
        "analyze_endpoint": "/analyze",
        "example_request": {
            "url": "https://acquire.com/",
            "debug": False
        }
    }

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_company(payload: AnalyzeRequest):
    url = payload.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    try:
        result = run_lead_brief_operator(url)
        logger.info(f"[API] /analyze called url={url} debug={payload.debug}")
        shaped = shape_operator_response(url, result, payload.debug)
        return shaped
    except Exception as e:
        logger.exception(f"[API] /analyze failed url={url} error={e}")
        return {
            "status": "failed",
            "source_url": url,
            "collection_status": None,
            "pages_collected": 0,
            "word_count": 0,
            "company_name": None,
            "what_they_sell": None,
            "target_customer": None,
            "business_model_guess": None,
            "positioning": None,
            "short_summary": None,
            "likely_bottleneck": None,
            "messaging_gap": None,
            "conversion_gap": None,
            "best_offer_angle": None,
            "final_output": None,
            "error_message": str(e),
            "debug_data": None,
        }

