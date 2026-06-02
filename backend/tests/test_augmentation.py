"""Тесты генерации обучающих данных: корректность спанов сущностей."""

import random

from src.use_cases.training.augmentation import build_sample, generate_dataset


def _assert_spans_tile_text(text: str, entities: list[tuple[int, int, str]]) -> None:
    """Проверяет инвариант: спаны идут подряд через одиночный пробел и покрывают всю строку."""
    # Конкатенация подстрок спанов через пробел должна давать исходный текст.
    assert ' '.join(text[start:end] for start, end, _ in entities) == text
    for start, end, _ in entities:
        assert 0 <= start < end <= len(text)
        assert text[start:end].strip() != ''


def test_spans_correct_without_noise() -> None:
    """Без шума спаны точно указывают на значения полей."""
    fields = {'BRAND': 'Супрастин', 'FORM': 'таблетки', 'DOSE': '25 мг', 'PACK': '№20'}
    text, entities = build_sample(fields, random.Random(1), noise=False)

    _assert_spans_tile_text(text, entities)
    # Множество значений в спанах совпадает с исходными полями (порядок перемешан).
    assert {text[s:e] for s, e, _ in entities} == set(fields.values())


def test_spans_correct_with_noise_and_collisions() -> None:
    """При коллизиях значений (10мг / 10 шт) и шуме спаны остаются корректными.

    Это главный регресс на баг наставника с raw_text.find().
    """
    fields = {'DOSE': '10мг', 'PACK': '10 шт'}
    for seed in range(300):
        text, entities = build_sample(fields, random.Random(seed), noise=True)
        _assert_spans_tile_text(text, entities)
        # Спаны не пересекаются.
        ordered = sorted(entities)
        for prev, current in zip(ordered, ordered[1:], strict=False):
            assert prev[1] <= current[0]


def test_generate_dataset_volume() -> None:
    """Размер датасета = записи × вариантов; первый вариант записи — без шума."""
    records = [{'A': 'альфа', 'B': 'бета'} for _ in range(3)]
    samples = generate_dataset(records, samples_per_record=5)

    assert len(samples) == 15
    # Хотя бы у части вариантов спаны валидны (выборочная проверка инварианта).
    for text, entities in samples:
        _assert_spans_tile_text(text, entities)
