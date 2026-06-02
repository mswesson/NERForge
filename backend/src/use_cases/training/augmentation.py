"""Генерация обучающего датасета из эталонных полей с внесением «шума».

Ключевой инвариант: спаны сущностей вычисляются ПРИ сборке строки из значений
(накопительным курсором), а не поиском по готовой строке. Поэтому для любого
сгенерированного примера всегда верно: text[start:end] == значение поля.
Шум вносится в значение ДО сборки строки, что сохраняет корректность спанов.
"""

import random

# Тип одного обучающего примера: текст и список спанов (start, end, LABEL).
Sample = tuple[str, list[tuple[int, int, str]]]


def drop_spaces(value: str, rng: random.Random) -> str:
    """Убирает внутренние пробелы значения (имитация «25 мг» → «25мг»)."""
    if ' ' not in value:
        return value
    return value.replace(' ', '') if rng.random() < 0.7 else value


def make_typo(value: str, rng: random.Random) -> str:
    """Вносит мелкую опечатку: перестановка двух соседних символов или удаление одного."""
    if len(value) < 4:
        return value
    chars = list(value)
    index = rng.randrange(len(chars) - 1)
    if rng.random() < 0.5:
        # Перестановка соседних символов.
        chars[index], chars[index + 1] = chars[index + 1], chars[index]
    else:
        # Удаление символа.
        del chars[index]
    return ''.join(chars)


def abbreviate(value: str, rng: random.Random) -> str:
    """Обрезает длинное слово до 3-4 букв (имитация «таблетки» → «таб»).

    Домен-независимое правило: сокращаем только достаточно длинные слова.
    """
    words = value.split(' ')
    changed = False
    for i, word in enumerate(words):
        if len(word) > 5 and rng.random() < 0.5:
            words[i] = word[: rng.randint(3, 4)]
            changed = True
    return ' '.join(words) if changed else value


def apply_noise(value: str, rng: random.Random) -> str:
    """Случайно применяет к значению несколько видов шума, не делая его пустым."""
    noised = value
    for transform in (drop_spaces, make_typo, abbreviate):
        if rng.random() < 0.4:
            candidate = transform(noised, rng)
            if candidate.strip():
                noised = candidate
    return noised if noised.strip() else value


def build_sample(fields: dict[str, str], rng: random.Random, *, noise: bool) -> Sample:
    """Собирает один пример: перемешивает поля, при noise=True вносит шум, считает спаны."""
    labels = list(fields.keys())
    rng.shuffle(labels)

    buffer: list[str] = []
    entities: list[tuple[int, int, str]] = []
    cursor = 0

    for i, label in enumerate(labels):
        value = apply_noise(fields[label], rng) if noise else fields[label]
        if i > 0:
            buffer.append(' ')
            cursor += 1
        start = cursor
        buffer.append(value)
        cursor += len(value)
        entities.append((start, cursor, label))

    return ''.join(buffer), entities


def generate_dataset(
    records: list[dict[str, str]],
    samples_per_record: int,
    seed: int = 42,
) -> list[Sample]:
    """Генерирует обучающий датасет: на каждую запись samples_per_record вариантов.

    Первый вариант каждой записи — «чистый» (без шума) как опорный, остальные — с шумом.
    """
    rng = random.Random(seed)
    dataset: list[Sample] = []

    for fields in records:
        if not fields:
            continue
        for index in range(samples_per_record):
            dataset.append(build_sample(fields, rng, noise=index > 0))

    return dataset
