"""Pydantic схемы фичи inference."""

from pydantic import BaseModel


class ParsedEntity(BaseModel):
    """Одна распознанная сущность в тексте."""

    label: str
    text: str
    start: int
    end: int


class ParseResponse(BaseModel):
    """Ответ эндпоинта POST /parse — разбивка текста по полям."""

    text: str
    entities: list[ParsedEntity]
    labels: list[str]
