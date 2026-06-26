import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from backend.rag_agent.vector_store import VectorStore
from backend.config import CONFIG


class Retriever:
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.top_k = CONFIG.rag.top_k

    def retrieve(self, query_vector: np.ndarray, top_k: Optional[int] = None, filter_source: Optional[str] = None) -> List[Tuple[str, float, Dict]]:
        k = top_k or self.top_k
        results = self.vector_store.search(query_vector, top_k=k * 2)

        if filter_source:
            results = [(k, s, m) for k, s, m in results if m.get("source") == filter_source]

        return results[:k]

    def hybrid_retrieve(self, query_vector: np.ndarray, keyword_score: Dict[str, float], top_k: Optional[int] = None) -> List[Tuple[str, float, Dict]]:
        k = top_k or self.top_k
        semantic_results = self.vector_store.search(query_vector, top_k=k * 3)

        combined = {}
        for key, score, meta in semantic_results:
            combined[key] = {"score": score * 0.7, "metadata": meta}
            if key in keyword_score:
                combined[key]["score"] += keyword_score[key] * 0.3

        ranked = sorted(combined.items(), key=lambda x: x[1]["score"], reverse=True)
        return [(key, data["score"], data["metadata"]) for key, data in ranked[:k]]
