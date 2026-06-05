from core.beat_schedule import BEAT_SCHEDULE


def test_beat_schedule_defined():
    from core.celery import app

    assert app.conf.beat_schedule is BEAT_SCHEDULE
    assert "nightly-stats" in BEAT_SCHEDULE

    entry = BEAT_SCHEDULE["nightly-stats"]
    assert entry["task"] == "features.analytics.infrastructure.tasks.calculate_daily_stats"

    schedule = entry["schedule"]
    assert schedule.hour == {2}
    assert schedule.minute == {0}
