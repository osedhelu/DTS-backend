from django.conf import settings


def test_celery_app_loads():
    from core.celery import app

    assert app.main == "dts"
    assert app.conf.broker_url == settings.CELERY_BROKER_URL
    assert app.conf.result_backend == settings.CELERY_RESULT_BACKEND
    assert app.conf.broker_url.startswith("redis://")
    assert app.conf.task_serializer == "json"
    assert app.conf.timezone == settings.TIME_ZONE
