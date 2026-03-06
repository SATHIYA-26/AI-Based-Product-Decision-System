from datetime import datetime, timedelta
from typing import List, Any


class TrendService:
    """Simple trend detection based on review timestamps.

    Assumes `timestamps` is a list of ISO8601 strings or datetime objects
    that are parallel to the original texts list. If a timestamp is None the
    review is ignored for trend calculation.

    The weekly growth score is computed as:
        growth = (recent_count - previous_count) / previous_count
    where "recent" means within the past 7 days and "previous" means the
    7–14 day window before now. The returned value is clipped to [0,1].
    """

    @staticmethod
    def _to_datetime(ts: Any) -> datetime | None:
        if ts is None:
            return None
        if isinstance(ts, datetime):
            return ts
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return None

    @staticmethod
    def compute_weekly_growth(indices: List[int], timestamps: List[Any]) -> float:
        now = datetime.utcnow()
        one_week = timedelta(days=7)

        recent_count = 0
        previous_count = 0

        for i in indices:
            dt = TrendService._to_datetime(timestamps[i])
            if not dt:
                continue
            delta = now - dt
            if delta <= one_week:
                recent_count += 1
            elif one_week < delta <= 2 * one_week:
                previous_count += 1

        if previous_count == 0:
            return 1.0 if recent_count > 0 else 0.0

        growth = (recent_count - previous_count) / previous_count
        # normalize to [0,1]
        growth = max(0.0, min(growth, 1.0))
        return growth
