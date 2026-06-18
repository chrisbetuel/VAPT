from abc import ABC, abstractmethod
from typing import Optional


class BaseScanner(ABC):
    name: str = ""
    description: str = ""
    docker_image: str = ""
    timeout: int = 300

    @abstractmethod
    async def scan(self, target: str, config: dict) -> list[dict]:
        pass

    async def validate_target(self, target: str) -> bool:
        return True

    async def parse_results(self, raw_output: str) -> list[dict]:
        return []
