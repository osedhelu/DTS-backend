from core.beat_schedule import BEAT_SCHEDULE


def test_beat_schedule_defined():
    from core.celery import app

    assert app.conf.beat_schedule is BEAT_SCHEDULE
    assert "nightly-stats" in BEAT_SCHEDULE
    assert "auto-assign-stale-orders" in BEAT_SCHEDULE

    entry = BEAT_SCHEDULE["nightly-stats"]
    assert entry["task"] == "features.analytics.infrastructure.tasks.calculate_daily_stats"

    stale = BEAT_SCHEDULE["auto-assign-stale-orders"]
    assert (
        stale["task"]
        == "features.delivery.infrastructure.tasks.auto_assign_stale_orders_task"
    )

    schedule = entry["schedule"]
    assert schedule.hour == {2}
    assert schedule.minute == {0}
