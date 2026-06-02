"""Пути к артефактам на диске: рабочие папки задач обучения и обученные модели."""

from pathlib import Path

from src.core.config import settings


def job_workdir(job_id: int) -> Path:
    """Рабочая папка задачи обучения (туда кладём train.spacy, dev.spacy, config.cfg)."""
    path = settings.jobs_dir / str(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def model_dir(model_id: int) -> Path:
    """Папка с артефактом обученной модели."""
    path = settings.models_dir / str(model_id)
    path.mkdir(parents=True, exist_ok=True)
    return path
