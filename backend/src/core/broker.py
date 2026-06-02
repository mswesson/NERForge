"""Инициализация RabbitMQ брокера через FastStream."""

from faststream.rabbit import RabbitBroker
from faststream.rabbit.schemas import Channel

from src.core.config import settings

broker = RabbitBroker(
    settings.RABBITMQ_URL,
    virtualhost=settings.RABBITMQ_VIRTUAL_HOST,
    default_channel=Channel(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT),
)
