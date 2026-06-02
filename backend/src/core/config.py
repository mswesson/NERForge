"""Настройки приложения через Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация сервиса из переменных окружения."""

    # Сервисные настройки
    SERVICE_NAME: str = 'NERForge'
    SERVICE_VERSION: str = '0.1.0'

    # База данных
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str

    # RabbitMQ
    RABBITMQ_URL: str
    RABBITMQ_VIRTUAL_HOST: str = '/'
    RABBITMQ_PREFETCH_COUNT: int = 1
    RABBITMQ_TRAINING_QUEUE: str = 'nerforge.training'

    # Хранилище артефактов (модели и рабочие папки задач обучения)
    DATA_DIR: Path = Path('/app/data')

    @property
    def database_url(self) -> str:
        """Строка подключения к PostgreSQL (asyncpg)."""
        return (
            f'postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}'
            f'@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}'
        )

    @property
    def models_dir(self) -> Path:
        """Папка с артефактами обученных моделей."""
        return self.DATA_DIR / 'models'

    @property
    def jobs_dir(self) -> Path:
        """Папка с рабочими директориями задач обучения."""
        return self.DATA_DIR / 'jobs'

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        env_prefix='NERFORGE_',
    )


settings = Settings()  # type: ignore
