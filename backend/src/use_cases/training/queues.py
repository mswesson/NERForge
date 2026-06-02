"""Очереди RabbitMQ для use_case training."""

from faststream.rabbit import QueueType, RabbitQueue

from src.core.config import settings

training_queue = RabbitQueue(
    settings.RABBITMQ_TRAINING_QUEUE,
    durable=True,
    queue_type=QueueType.QUORUM,
)
