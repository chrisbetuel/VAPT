from app.scanners.base import BaseScanner


class NucleiScanner(BaseScanner):
    name = "nuclei"
    description = "Nuclei - Vulnerability scanner based on YAML templates"
    docker_image = "projectdiscovery/nuclei:latest"

    async def scan(self, target: str, config: dict) -> list[dict]:
        pass
