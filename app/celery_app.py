from celery import Celery

celery_app = Celery("servit")
celery_app.conf.update(
    broker_url="amqp://guest:guest@localhost:5672//",
    result_backend="rpc://",
    task_serializer="json",
    accept_content=["json"],
)

celery_app.autodiscover_tasks(["app.tasks"])
