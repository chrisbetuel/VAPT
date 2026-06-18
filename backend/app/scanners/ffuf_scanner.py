from app.scanners.base import BaseScanner


class FFUFScanner(BaseScanner):
    name = "ffuf"
    description = "FFUF - Fast web fuzzer for directory/file enumeration"
    docker_image = "sdeckers/ffuf:latest"

    async def scan(self, target: str, config: dict) -> list[dict]:
        pass
