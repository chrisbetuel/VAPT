from app.scanners.base import BaseScanner


class SubfinderScanner(BaseScanner):
    name = "subfinder"
    description = "Subfinder - Passive subdomain enumeration"
    docker_image = "projectdiscovery/subfinder:latest"

    async def scan(self, target: str, config: dict) -> list[dict]:
        pass
