"""Тесты генерации датасета и сборки обучающих примеров."""

from src.features.dataset.service import (
    _ORDER_COLUMN,
    _assemble_from_order,
    build_training_samples,
    generate_rows,
)


def _assert_spans_tile_text(text: str, entities: list[tuple[int, int, str]]) -> None:
    """Инвариант: конкатенация спанов через пробел даёт исходный текст; спаны валидны."""
    assert ' '.join(text[start:end] for start, end, _ in entities) == text
    for start, end, _ in entities:
        assert 0 <= start < end <= len(text)
        assert text[start:end].strip() != ''


def test_assemble_respects_order() -> None:
    """Сборка идёт строго в заданном порядке, спаны корректны."""
    fields = {'BRAND': 'Супрастин', 'DOSE': '10мг', 'PACK': '10 шт'}
    text, entities = _assemble_from_order(fields, ['PACK', 'BRAND', 'DOSE'])

    assert text == '10 шт Супрастин 10мг'
    assert [label for *_, label in entities] == ['PACK', 'BRAND', 'DOSE']
    _assert_spans_tile_text(text, entities)


def test_generate_rows_volume_and_anchor() -> None:
    """Размер = записи × вариаций; первая вариация чистая и в исходном порядке."""
    records = [{'BRAND': 'Супрастин', 'FORM': 'таблетки', 'DOSE': '25 мг'} for _ in range(4)]
    rows = generate_rows(
        records,
        5,
        noise_ratio=0.5,
        typo_ratio=0.2,
        remove_whitespaces=True,
        truncate_words=True,
        shuffle_order=True,
    )

    assert len(rows) == 20
    assert all(_ORDER_COLUMN in row for row in rows)
    # Первая вариация записи — исходный порядок и неизменённые значения.
    assert rows[0][_ORDER_COLUMN] == 'BRAND FORM DOSE'
    assert rows[0]['BRAND'] == 'Супрастин'


def test_training_uses_data_as_is() -> None:
    """Сборка примеров идёт строго по _ORDER_COLUMN — ничего не перемешивает."""
    rows = [
        {'BRAND': 'Супрастин', 'DOSE': '10мг', 'PACK': '10 шт', _ORDER_COLUMN: 'pack brand dose'}
    ]
    samples = build_training_samples(rows)

    assert len(samples) == 1
    text, entities = samples[0]
    assert text == '10 шт Супрастин 10мг'
    _assert_spans_tile_text(text, entities)


def test_collisions_spans_correct() -> None:
    """Совпадающие значения (10 / 10) не ломают спаны — регресс на баг с find()."""
    rows = [{'DOSE': '10', 'PACK': '10', _ORDER_COLUMN: 'dose pack'}]
    text, entities = build_training_samples(rows)[0]

    assert text == '10 10'
    assert entities[0] == (0, 2, 'DOSE')
    assert entities[1] == (3, 5, 'PACK')
