"""HTTP API фичи datasets."""

from fastapi import APIRouter, Depends, File, Query, UploadFile

from src.core.exceptions import DatasetNotFoundError
from src.features.datasets.schemas import (
    DatasetGetResponse,
    DatasetListResponse,
    DatasetUploadResponse,
)
from src.features.datasets.service import DatasetService, get_dataset_service

router = APIRouter(prefix='/datasets', tags=['Датасеты'])


@router.post('/', response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(..., description='CSV: первая колонка — id, остальные — поля'),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetUploadResponse:
    """Загружает CSV и сохраняет датасет с эталонными записями."""
    content = await file.read()
    dataset = await service.upload(name=file.filename or 'dataset.csv', content=content)
    return DatasetUploadResponse.model_validate(dataset)


@router.get('/', response_model=DatasetListResponse)
async def list_datasets(
    page: int = Query(1, ge=1, description='Номер страницы', example=1),
    page_size: int = Query(50, ge=1, le=500, description='Записей на странице', example=50),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetListResponse:
    """Возвращает постраничный список датасетов."""
    return await service.get_list(page=page, page_size=page_size)


@router.get('/{dataset_id}', response_model=DatasetGetResponse)
async def get_dataset(
    dataset_id: int,
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetGetResponse:
    """Возвращает один датасет по идентификатору."""
    dataset = await service.get_by_id(dataset_id)
    if dataset is None:
        raise DatasetNotFoundError(f'Датасет {dataset_id} не найден.')
    return DatasetGetResponse.model_validate(dataset)
