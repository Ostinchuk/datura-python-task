from celery import Celery

from app.core.settings import settings

celery_app = Celery(
    "bittensor_api",
    broker=settings.CACHE_SERVER_URL,
    backend=settings.CACHE_SERVER_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_hijack_root_logger=False,
    task_track_started=True,
    task_time_limit=300,
)

celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task
def run_async_task(coro_function_path, *args, **kwargs):
    """
    Helper task to run async functions in Celery.
    coro_function_path should be a string like "app.tasks.sentiment.execute_sentiment_analysis"
    """
    import asyncio
    import importlib

    module_path, function_name = coro_function_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    coro_function = getattr(module, function_name)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro_function(*args, **kwargs))
