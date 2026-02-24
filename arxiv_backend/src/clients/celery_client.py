from celery import Celery


class CeleryClient:
    def __init__(self, app: Celery):
        self.app = app

    def send_task(self, task_name: str, task_id: str, kwargs: dict):
        return self.app.send_task(
            task_name,
            kwargs=kwargs,
            task_id=task_id,
        )
