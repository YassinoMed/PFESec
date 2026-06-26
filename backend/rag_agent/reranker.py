from typing import Any, Dict, List, Tuple


class Reranker:
    def __init__(self):
        self.boost_factors = {
            "mitre_attck": 1.3,
            "cve": 1.2,
            "sigma": 1.1,
            "runbooks": 1.15,
            "misp": 1.05,
        }

    def rerank(self, results: List[Tuple[str, float, Dict]], query: str = "") -> List[Tuple[str, float, Dict]]:
        if not results:
            return results

        scored = []
        for key, score, metadata in results:
            boosted = score

            source = metadata.get("source", "")
            boost = self.boost_factors.get(source, 1.0)
            boosted *= boost

            recency = metadata.get("recency", 0.5)
            boosted *= (0.8 + 0.4 * recency)

            scored.append((key, round(boosted, 4), metadata))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def set_boost(self, source: str, factor: float):
        self.boost_factors[source] = factor
