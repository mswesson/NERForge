"""Доменные исключения приложения (без привязки к HTTP)."""


class DomainError(Exception):
    """Базовое доменное исключение."""


class EmptyDatasetError(DomainError):
    """CSV не содержит валидных записей или полей-меток."""


class TrainingJobNotFoundError(DomainError):
    """Задача обучения с указанным идентификатором не найдена."""


class ModelNotFoundError(DomainError):
    """Модель с указанным идентификатором не найдена или не готова."""


class BaseModelUnavailableError(DomainError):
    """Выбранная базовая модель spaCy не установлена в окружении."""
