"""Inference: загрузка spaCy-модели с кэшем и разбор текста на сущности."""

import functools

import spacy
from spacy.language import Language


@functools.lru_cache(maxsize=8)
def _load_nlp(artifact_path: str) -> Language:
    """Загружает spaCy-модель с диска (кэш по пути артефакта)."""
    return spacy.load(artifact_path)


def parse_text(
    artifact_path: str, text: str, label_names: list[str]
) -> tuple[dict[str, str | None], list[dict]]:
    """Разбирает текст моделью: возвращает поля по меткам и список сущностей.

    Это блокирующая CPU-операция — вызывать через asyncio.to_thread.
    """
    nlp = _load_nlp(artifact_path)
    doc = nlp(text)

    # По умолчанию все метки пустые.
    fields: dict[str, str | None] = {label: None for label in label_names}
    entities: list[dict] = []

    for ent in doc.ents:
        entities.append(
            {'label': ent.label_, 'text': ent.text, 'start': ent.start_char, 'end': ent.end_char}
        )
        # Первое вхождение метки заполняет поле.
        if ent.label_ in fields and fields[ent.label_] is None:
            fields[ent.label_] = ent.text

    return fields, entities
