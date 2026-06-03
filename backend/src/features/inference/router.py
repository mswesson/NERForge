"""HTTP API шага 3: разбор текста загруженной моделью."""

from fastapi import APIRouter, File, Form, UploadFile

from src.features.inference.schemas import ParseResponse
from src.features.inference.service import inference_service

router = APIRouter(prefix='/parse', tags=['Разбор'])


@router.post('/', response_model=ParseResponse)
async def parse_text(
    model: UploadFile = File(..., description='zip обученной модели (model-best)'),
    text: str = Form(..., description='Текст для разбиения на поля'),
) -> ParseResponse:
    """Принимает zip модели и текст, возвращает разбивку по полям."""
    zip_bytes = await model.read()
    return await inference_service.parse(zip_bytes, text)
