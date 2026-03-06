import re
from typing import List


class DataFilterService:

    @staticmethod
    def filter_reviews(reviews: List) -> List:
        """
        Clean and filter low-quality reviews before NLP processing.  Supports
        either a list of strings or a list of dicts with ``text`` and optional
        ``timestamp``. Returns the items in the same shape as the input so that
        timestamps are preserved for downstream trend detection.
        """

        filtered = []
        seen = set()

        for item in reviews:
            if isinstance(item, dict):
                review = item.get("text", "")
                ts = item.get("timestamp")
            else:
                review = item
                ts = None

            if not review:
                continue

            review = review.strip()

            # Remove excessive symbols
            review = re.sub(r"[^\w\s]", "", review)

            # Remove extra spaces
            review = re.sub(r"\s+", " ", review)

            # Rule 1: Minimum length (at least 3 words)
            if len(review.split()) < 3:
                continue

            # Rule 2: Remove duplicates
            lowered = review.lower()
            if lowered in seen:
                continue

            seen.add(lowered)

            if ts is not None:
                filtered.append({"text": review, "timestamp": ts})
            else:
                filtered.append(review)

        return filtered
