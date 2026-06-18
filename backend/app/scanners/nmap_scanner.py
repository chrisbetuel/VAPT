from app.scanners.base import BaseScanner


class NmapScanner(BaseScanner):
    name = "nmap"
    description = "Nmap - Network discovery and port scanning"
    docker_image = "instrumentisto/nmap:latest"

    async def scan(self, target: str, config: dict) -> list[dict]:
        pass
