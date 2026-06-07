"""HTTP API шага 1: генерация обучающего JSONL-датасета."""

import io

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import StreamingResponse

from src.features.dataset.service import generation_service

router = APIRouter(prefix='/generate', tags=['Генерация'])


@router.post('/')
async def generate_dataset(
    file: UploadFile = File(..., description='Эталонный CSV (колонки = метки, без id)'),
    variations_per_row: int = Form(5, ge=1, le=200, description='Вариаций на каждую строку'),
    noise_ratio: float = Form(0.4, ge=0.0, le=1.0, description='Доля зашумлённых вариаций'),
    typo_ratio: float = Form(0.15, ge=0.0, le=1.0, description='Вероятность опечаток'),
    remove_whitespaces: bool = Form(True, description='Сжимать пробелы (25 мг → 25мг)'),
    truncate_words: bool = Form(True, description='Сокращать слова (таблетки → таб)'),
    shuffle_order: bool = Form(True, description='Перемешивать порядок полей в вариациях'),
    lowercase: bool = Form(False, description='Привести все значения к нижнему регистру'),
) -> StreamingResponse:
    """Генерирует обучающий JSONL (вариации на строку) и отдаёт на скачивание."""
    content = await file.read()
    result = generation_service.generate(
        content,
        variations_per_row=variations_per_row,
        noise_ratio=noise_ratio,
        typo_ratio=typo_ratio,
        remove_whitespaces=remove_whitespaces,
        truncate_words=truncate_words,
        shuffle_order=shuffle_order,
        lowercase=lowercase,
    )
    return StreamingResponse(
        io.BytesIO(result),
        media_type='application/x-ndjson',
        headers={'Content-Disposition': 'attachment; filename=nerforge_dataset.jsonl'},
    )
