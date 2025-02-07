from celery import Celery
from celery.schedules import crontab

celery_app = Celery("servit")
celery_app.conf.update(
    broker_url="amqp://guest:guest@localhost:5672//",
    result_backend="rpc://",
    task_serializer="json",
    accept_content=["json"],
)

celery_app.conf.beat_schedule = {
    "delete_old_logs_daily": {
        "task": "app.tasks.delete_old_logs.delete_old_logs",
        "schedule": crontab(minute="0", hour="0"),
    },
}

celery_app.autodiscover_tasks(["app.tasks"])
