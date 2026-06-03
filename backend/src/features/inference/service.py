"""Бизнес-логика фичи inference: разбор текста загруженной моделью."""

import asyncio

from src.features.inference.inference import parse_uploaded
from src.features.inference.schemas import ParsedEntity, ParseResponse


class InferenceService:
    """Сервис разбора текста stateless-моделью из zip."""

    @staticmethod
    async def parse(zip_bytes: bytes, text: str) -> ParseResponse:
        """Разбирает текст загруженной моделью на сущности."""
        # Загрузка модели и инференс — блокирующие, уносим в отдельный поток.
        entities, labels = await asyncio.to_thread(parse_uploaded, zip_bytes, text)
        return ParseResponse(
            text=text,
            entities=[ParsedEntity(**ent) for ent in entities],
            labels=labels,
        )


inference_service = InferenceService()
