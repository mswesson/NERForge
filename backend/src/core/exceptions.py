"""Доменные исключения приложения (без привязки к HTTP)."""


class DomainError(Exception):
    """Базовое доменное исключение."""


class DatasetNotFoundError(DomainError):
    """Датасет с указанным идентификатором не найден."""


class EmptyDatasetError(DomainError):
    """CSV не содержит валидных записей или полей-меток."""


class TrainingJobNotFoundError(DomainError):
    """Задача обучения с указанным идентификатором не найдена."""


class ModelNotFoundError(DomainError):
    """Модель с указанным идентификатором не найдена или не готова."""
