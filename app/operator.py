from app.site_collector import collect_site
from app.business_analyzer import analyze_business
from app.outreach_writer import write_outreach
from app.final_formatter import format_final_report
import time
from app.logger import get_logger

logger = get_logger("operator")


def run_lead_brief_operator(url: str) -> dict:
    start_time = time.perf_counter()
    logger.info(f"[REQUEST] Started url={url}")

    try:
        collector_start = time.perf_counter()
        logger.info("[COLLECTOR] Starting")
        collector_result = collect_site(url)
        collector_duration = time.perf_counter() - collector_start

        logger.info(
            f"[COLLECTOR] status={collector_result['status']} "
            f"duration={collector_duration:.2f}s"
        )

        if collector_result["status"] != "ok":
            total_duration = time.perf_counter() - start_time
            logger.warning(
                f"[REQUEST] Failed at collector url={url} duration={total_duration:.2f}s"
            )
            return {
                "tool": "operator",
                "status": "failed",
                "message": collector_result["message"],
                "data": {
                    "collector": collector_result,
                    "analyzer": None,
                    "writer": None,
                    "formatter": None,
                },
            }

        combined_text = collector_result["data"]["combined_text"]

        analyzer_start = time.perf_counter()
        logger.info("[ANALYZER] Starting")
        analyzer_result = analyze_business(combined_text, url)
        analyzer_duration = time.perf_counter() - analyzer_start

        logger.info(
            f"[ANALYZER] status={analyzer_result['status']} "
            f"duration={analyzer_duration:.2f}s"
        )

        if analyzer_result["status"] != "ok":
            total_duration = time.perf_counter() - start_time
            if analyzer_duration > 8:
                logger.warning(f"[ANALYZER] Slow stage duration={analyzer_duration:.2f}s")
            logger.warning(
                f"[REQUEST] Failed at analyzer url={url} duration={total_duration:.2f}s"
            )
            return {
                "tool": "operator",
                "status": "failed",
                "message": analyzer_result["message"],
                "data": {
                    "collector": collector_result,
                    "analyzer": analyzer_result,
                    "writer": None,
                    "formatter": None,
                },
            }

        writer_start = time.perf_counter()
        logger.info("[WRITER] Starting")
        writer_result = write_outreach(analyzer_result["data"], url)
        writer_duration = time.perf_counter() - writer_start
        if writer_duration > 4:
            logger.warning(f"[WRITER] Slow stage duration={writer_duration:.2f}s")

        logger.info(
            f"[WRITER] status={writer_result['status']} "
            f"duration={writer_duration:.2f}s"
        )

        formatter_start = time.perf_counter()
        logger.info("[FORMATTER] Starting")
        formatter_result = format_final_report(url, collector_result, analyzer_result, writer_result)
        formatter_duration = time.perf_counter() - formatter_start

        logger.info(
            f"[FORMATTER] status={formatter_result['status']} "
            f"duration={formatter_duration:.2f}s"
        )

        total_duration = time.perf_counter() - start_time
        if total_duration > 12:
            logger.warning(f"[REQUEST] Slow total duration={total_duration:.2f}s url={url}")
        logger.info(
            f"[REQUEST] Completed url={url} status=ok duration={total_duration:.2f}s"
        )

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

    except Exception as e:
        total_duration = time.perf_counter() - start_time
        logger.exception(
            f"[REQUEST] Crashed url={url} duration={total_duration:.2f}s error={e}"
        )
        raise