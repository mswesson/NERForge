"""Публикация сообщений о запуске обучения в RabbitMQ."""

from src.core.broker import broker
from src.use_cases.training.queues import training_queue
from src.use_cases.training.schemas import TrainingTaskMessage


async def publish_training_task(job_id: int) -> None:
    """Кладёт задачу обучения в очередь."""
    await broker.publish(TrainingTaskMessage(job_id=job_id), queue=training_queue)
