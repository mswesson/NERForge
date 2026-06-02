"""HTTP API фичи models."""

from fastapi import APIRouter, Depends, Query

from src.core.exceptions import ModelNotFoundError
from src.features.models.schemas import (
    ModelGetResponse,
    ModelListResponse,
    ParseRequest,
    ParseResponse,
)
from src.features.models.service import ModelService, get_model_service

router = APIRouter(prefix='/models', tags=['Модели'])


@router.get('/', response_model=ModelListResponse)
async def list_models(
    page: int = Query(1, ge=1, description='Номер страницы', example=1),
    page_size: int = Query(50, ge=1, le=500, description='Записей на странице', example=50),
    service: ModelService = Depends(get_model_service),
) -> ModelListResponse:
    """Возвращает постраничный список обученных моделей."""
    return await service.get_list(page=page, page_size=page_size)


@router.get('/{model_id}', response_model=ModelGetResponse)
async def get_model(
    model_id: int,
    service: ModelService = Depends(get_model_service),
) -> ModelGetResponse:
    """Возвращает одну модель по идентификатору."""
    model = await service.get_by_id(model_id)
    if model is None:
        raise ModelNotFoundError(f'Модель {model_id} не найдена.')
    return ModelGetResponse.model_validate(model)


@router.post('/{model_id}/parse', response_model=ParseResponse)
async def parse_string(
    model_id: int,
    payload: ParseRequest,
    service: ModelService = Depends(get_model_service),
) -> ParseResponse:
    """Разбирает произвольный текст указанной моделью на поля."""
    return await service.parse(model_id=model_id, text=payload.text)
