from datetime import datetime, timedelta, timezone

# The Philippines has no daylight saving time, so a fixed UTC+8 offset is exact
# and avoids needing the tzdata package on Windows.
PH_TZ = timezone(timedelta(hours=8), "Asia/Manila")


def now_ph() -> datetime:
    """The single source of "now" for the whole app (timezone-aware, PH time)."""
    return datetime.now(PH_TZ)
