"""Consumer RabbitMQ: запуск обучения по задаче из очереди."""

from faststream import AckPolicy
from loguru import logger

from src.core.broker import broker
from src.use_cases.training.models import TrainingStatus
from src.use_cases.training.queues import training_queue
from src.use_cases.training.schemas import TrainingTaskMessage
from src.use_cases.training.service import _update, run_training_job


@broker.subscriber(training_queue, ack_policy=AckPolicy.REJECT_ON_ERROR)
async def handle_training(message: TrainingTaskMessage) -> None:
    """Принимает задачу и запускает обучение.

    При ошибке фиксируем статус failed и подтверждаем сообщение (ACK): повторный
    прогон детерминированно упавшей задачи бесполезен и только зациклит очередь.
    """
    try:
        await run_training_job(message.job_id)
    except Exception as error:
        logger.exception('Обучение упало', job_id=message.job_id)
        await _update(
            message.job_id,
            status=TrainingStatus.FAILED,
            error=str(error),
        )
