import json
from pathlib import Path

from typing import Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.operator import run_lead_brief_operator

from app.config import settings

app = FastAPI(title="Lead Brief Operator API")

JOBS_PATH = Path(settings.JOBS_PATH)


def load_jobs() -> dict:
    if not JOBS_PATH.exists():
        return {}

    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jobs(jobs_data: dict) -> None:
    JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(JOBS_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs_data, f, ensure_ascii=False, indent=2)

# in-memory job store
jobs = load_jobs()


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


def run_analysis_job(job_id: str, url: str, debug: bool):
    try:
        jobs[job_id]["status"] = "running"
        save_jobs(jobs)

        raw_result = run_lead_brief_operator(url)
        shaped_result = shape_operator_response(url, raw_result, debug)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = shaped_result
        jobs[job_id]["error"] = None
        save_jobs(jobs)

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["result"] = None
        jobs[job_id]["error"] = str(e)
        save_jobs(jobs)


@app.get("/")
def root():
    return {
        "message": "Lead Brief Operator API is running."
    }


@app.post("/analyze", response_model=AnalyzeAcceptedResponse)
def analyze_company(payload: AnalyzeRequest, background_tasks: BackgroundTasks):
    url = payload.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    job_id = str(uuid4())

    jobs[job_id] = {
        "status": "accepted",
        "url": url,
        "result": None,
        "error": None,
        "debug": payload.debug,
    }

    save_jobs(jobs)

    background_tasks.add_task(run_analysis_job, job_id, url, payload.debug)

    return {
        "job_id": job_id,
        "status": "accepted",
    }


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    job = jobs.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "error": job["error"],
    }