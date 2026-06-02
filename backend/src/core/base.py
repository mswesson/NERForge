"""Коллектор импортов моделей для Alembic autogenerate."""

from src.core.database import Base  # noqa: F401
from src.features.datasets.models import Dataset, DatasetRecord  # noqa: F401
from src.features.models.models import Model  # noqa: F401
from src.use_cases.training.models import TrainingJob  # noqa: F401

__all__ = ['Base']
