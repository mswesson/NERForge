"""Пути к артефактам на диске и очистка (храним только последний результат)."""

import shutil
from pathlib import Path

from src.core.config import settings


def reset_jobs_dir() -> None:
    """Полностью очищает папку задач обучения — копим только последний результат."""
    shutil.rmtree(settings.jobs_dir, ignore_errors=True)
    settings.jobs_dir.mkdir(parents=True, exist_ok=True)


def job_workdir(job_id: int) -> Path:
    """Рабочая папка задачи обучения (train.spacy, dev.spacy, config.cfg, output, zip)."""
    path = settings.jobs_dir / str(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def reset_uploaded_models_dir() -> None:
    """Полностью очищает папку загруженных моделей — храним только последнюю."""
    shutil.rmtree(settings.uploaded_models_dir, ignore_errors=True)
    settings.uploaded_models_dir.mkdir(parents=True, exist_ok=True)
