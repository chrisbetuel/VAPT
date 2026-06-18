from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def generate_report(self, report_id: int):
    pass


@celery_app.task
def send_scheduled_reports():
    pass


@celery_app.task
def export_report_to_format(report_id: int, fmt: str):
    pass
