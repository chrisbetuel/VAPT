from fastapi import APIRouter, Depends
from app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookEvent
from app.services.webhook_service import WebhookService
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=list[WebhookResponse])
async def list_webhooks(db: AsyncSession = Depends(get_db)):
    pass


@router.post("/", response_model=WebhookResponse, status_code=201)
async def create_webhook(webhook: WebhookCreate, db: AsyncSession = Depends(get_db)):
    pass


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: int, db: AsyncSession = Depends(get_db)):
    pass


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: int, db: AsyncSession = Depends(get_db)):
    pass
