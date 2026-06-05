from django.conf import settings

from features.analytics.infrastructure.tasks import calculate_daily_stats


def test_celery_eager_settings_enabled():
    assert settings.CELERY_TASK_ALWAYS_EAGER is True
    assert settings.CELERY_TASK_EAGER_PROPAGATES is True


def test_celery_tasks_run_synchronously_in_tests():
    result = calculate_daily_stats.delay()

    assert result.successful()
    assert result.get(timeout=1) == "pending"
