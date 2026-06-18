from sqlalchemy.ext.asyncio import AsyncSession


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self):
        pass

    async def get_recent_scans(self):
        pass

    async def get_vulnerability_summary(self):
        pass

    async def get_vulnerability_trends(self):
        pass
