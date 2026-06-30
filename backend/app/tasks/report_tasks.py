import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.core.celery_app import celery_app
from app.core.database import SyncSession
from app.models.report import Report, ReportStatus
from app.services.report_service import build_report_data

logger = logging.getLogger(__name__)

REPORTS_DIR = Path("/app/reports")
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_id: int):
    session = SyncSession()
    try:
        report = session.get(Report, report_id)
        if not report:
            logger.error("Report %d not found", report_id)
            return {"error": "Report not found"}

        report.status = ReportStatus.GENERATING
        session.commit()

        data = build_report_data(report)
        data = data or {}

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        formats = report.formats or {}
        if isinstance(formats, dict):
            for fmt in formats:
                try:
                    _generate_format(report_id, fmt, data)
                    formats[fmt] = "completed"
                except Exception as e:
                    logger.exception("Failed to generate %s for report %d", fmt, report_id)
                    formats[fmt] = f"error: {str(e)}"

        report.formats = formats
        report.status = ReportStatus.COMPLETED
        report.completed_at = datetime.now(timezone.utc)
        session.commit()

        logger.info("Report %d generated successfully", report_id)
        return {"status": "completed", "report_id": report_id}

    except Exception as exc:
        logger.exception("Report %d generation failed", report_id)
        session.rollback()
        try:
            report = session.get(Report, report_id)
            if report:
                report.status = ReportStatus.ERROR
                session.commit()
        except Exception:
            session.rollback()
        raise self.retry(exc=exc)
    finally:
        session.close()


def _generate_format(report_id: int, fmt: str, data: dict):
    if fmt == "html":
        _generate_html(report_id, data)
    elif fmt == "pdf":
        _generate_pdf(report_id, data)
    elif fmt == "json":
        _generate_json(report_id, data)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def _generate_html(report_id: int, data: dict):
    template = env.get_template("report.html")
    html = template.render(**data)
    out_path = REPORTS_DIR / f"report_{report_id}.html"
    out_path.write_text(html, encoding="utf-8")
    logger.info("HTML report written to %s", out_path)


def _generate_pdf(report_id: int, data: dict):
    template = env.get_template("report.html")
    html = template.render(**data)

    try:
        from weasyprint import HTML
        out_path = REPORTS_DIR / f"report_{report_id}.pdf"
        HTML(string=html).write_pdf(str(out_path))
        logger.info("PDF report written to %s", out_path)
    except ImportError:
        logger.warning("weasyprint not available, falling back to HTML-only")
        _generate_html(report_id, data)


def _generate_json(report_id: int, data: dict):
    out_path = REPORTS_DIR / f"report_{report_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("JSON report written to %s", out_path)


@celery_app.task
def send_scheduled_reports():
    pass


@celery_app.task
def export_report_to_format(report_id: int, fmt: str):
    generate_report.delay(report_id)
