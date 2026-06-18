from sqlalchemy.ext.asyncio import AsyncSession


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(self):
        pass

    async def list_webhooks(self):
        pass

    async def delete_webhook(self, webhook_id: int):
        pass

    async def test_webhook(self, webhook_id: int):
        pass
