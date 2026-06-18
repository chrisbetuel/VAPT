from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_report(self):
        pass

    async def get_report(self, report_id: int):
        pass

    async def list_reports(self):
        pass

    async def download_report(self, report_id: int, fmt: str):
        pass

    async def delete_report(self, report_id: int):
        pass
