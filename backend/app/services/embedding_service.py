# app/services/embedding_service.py

import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer


class EmbeddingService:

    _model = SentenceTransformer("all-MiniLM-L6-v2")

    @classmethod
    def generate_embeddings(cls, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        
        embeddings = cls._model.encode(texts, convert_to_numpy=True)
        return embeddings
