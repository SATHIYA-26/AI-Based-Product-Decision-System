# app/services/priority_service.py

from typing import Dict


class PriorityService:

    @staticmethod
    def normalize(value: float, max_value: float) -> float:
        if max_value == 0:
            return 0.0
        return value / max_value

    @staticmethod
    def compute_priority(
        frequency: int,
        max_frequency: int,
        avg_sentiment: float,
        trend_score: float,
        freq_weight: float = 0.5,
        sentiment_weight: float = 0.3,
        trend_weight: float = 0.2
    ) -> float:

        normalized_freq = PriorityService.normalize(frequency, max_frequency)

        severity = abs(min(avg_sentiment, 0))  # only negative impact
        normalized_severity = min(severity, 1)

        normalized_trend = min(max(trend_score, 0), 1)

        score = (
            freq_weight * normalized_freq +
            sentiment_weight * normalized_severity +
            trend_weight * normalized_trend
        )

        return round(score * 100, 2)
