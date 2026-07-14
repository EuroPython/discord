import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnimalImage:
    url: str
    source: str


class AnimalImageProvider(ABC):
    @abstractmethod
    async def generate_image(self) -> AnimalImage | None: ...
