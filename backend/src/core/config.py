"""Настройки приложения через Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация сервиса из переменных окружения."""

    # Сервисные настройки
    SERVICE_NAME: str = 'NERForge'
    SERVICE_VERSION: str = '0.1.0'

    # Хранилище артефактов (рабочие папки обучения и загруженные модели)
    DATA_DIR: Path = Path('./data')

    # CORS: список origin'ов фронтенда (JSON-массив в env).
    CORS_ORIGINS: list[str] = ['http://localhost:3000']

    @property
    def jobs_dir(self) -> Path:
        """Папка с рабочей директорией текущей задачи обучения."""
        return self.DATA_DIR / 'jobs'

    @property
    def uploaded_models_dir(self) -> Path:
        """Папка с распакованной загруженной моделью для парсинга."""
        return self.DATA_DIR / 'uploaded_models'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        env_prefix='NERFORGE_',
        extra='ignore',  # не падать на устаревших переменных в .env
    )


settings = Settings()
