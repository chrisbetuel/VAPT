from app.core.celery_app import celery_app


@celery_app.task
def send_scan_completed_notification(scan_id: int):
    pass


@celery_app.task
def send_critical_vulnerability_alert(scan_id: int, vulnerability_id: int):
    pass


@celery_app.task
def send_webhook_event(event_type: str, payload: dict):
    pass


@celery_app.task
def send_email_notification(recipient: str, subject: str, body: str):
    pass
