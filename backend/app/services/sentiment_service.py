# app/services/sentiment_service.py

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List


class SentimentService:

    _analyzer = SentimentIntensityAnalyzer()

    @classmethod
    def compute_sentiment(cls, text: str) -> float:
        if not text:
            return 0.0

        score = cls._analyzer.polarity_scores(text)
        return score["compound"]

    @classmethod
    def batch_sentiment(cls, texts: List[str]) -> List[float]:
        return [cls.compute_sentiment(t) for t in texts]
