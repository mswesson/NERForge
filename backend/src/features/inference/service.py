"""Сервис разбора текста загруженной spaCy-моделью.

Храним только ОДНУ — последнюю — загруженную модель. При загрузке новой (с другим
содержимым) предыдущая распакованная модель удаляется с диска.
"""

import asyncio
import hashlib
import io
import zipfile

import spacy
from spacy.language import Language

from src.core import storage
from src.core.config import settings
from src.features.inference.schemas import ParsedEntity, ParseResponse

# Текущая загруженная модель: хэш содержимого и сам объект.
_current: dict[str, object] = {'digest': None, 'nlp': None}


def _load_from_zip(zip_bytes: bytes) -> Language:
    """Распаковывает и загружает модель, очищая предыдущую при смене содержимого."""
    digest = hashlib.sha256(zip_bytes).hexdigest()
    if _current['digest'] == digest and _current['nlp'] is not None:
        return _current['nlp']  # type: ignore[return-value]

    storage.reset_uploaded_models_dir()
    target = settings.uploaded_models_dir / digest
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        archive.extractall(target)

    nlp = spacy.load(target)
    _current['digest'] = digest
    _current['nlp'] = nlp
    return nlp


def _parse_uploaded(zip_bytes: bytes, text: str) -> tuple[list[dict], list[str]]:
    """Разбирает текст загруженной моделью: возвращает сущности и список меток модели.

    Это блокирующая CPU-операция — вызывать через asyncio.to_thread.
    """
    nlp = _load_from_zip(zip_bytes)
    doc = nlp(text)

    entities = [
        {'label': ent.label_, 'text': ent.text, 'start': ent.start_char, 'end': ent.end_char}
        for ent in doc.ents
    ]
    ner = nlp.get_pipe('ner') if 'ner' in nlp.pipe_names else None
    labels = list(ner.labels) if ner is not None else []
    return entities, labels


class InferenceService:
    """Сервис разбора текста stateless-моделью из zip."""

    @staticmethod
    async def parse(zip_bytes: bytes, text: str) -> ParseResponse:
        """Разбирает текст загруженной моделью на сущности."""
        entities, labels = await asyncio.to_thread(_parse_uploaded, zip_bytes, text)
        return ParseResponse(
            text=text,
            entities=[ParsedEntity(**ent) for ent in entities],
            labels=labels,
        )


inference_service = InferenceService()
