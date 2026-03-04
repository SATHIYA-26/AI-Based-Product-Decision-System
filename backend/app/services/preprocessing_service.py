# app/services/preprocessing_service.py

import re
import spacy
from typing import List

nlp = spacy.load("en_core_web_sm")


class PreprocessingService:

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        text = text.lower()
        text = re.sub(r"http\S+|www\S+", "", text)
        text = re.sub(r"<.*?>", "", text)
        text = re.sub(r"[^a-zA-Z\s]", "", text)

        doc = nlp(text)

        tokens = [
            token.lemma_
            for token in doc
            if not token.is_stop and not token.is_punct
        ]

        return " ".join(tokens).strip()

    @staticmethod
    def batch_clean(texts: List[str]) -> List[str]:
        return [PreprocessingService.clean_text(t) for t in texts]
