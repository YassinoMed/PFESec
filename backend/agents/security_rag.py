import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from backend.agents.base import BaseAgent, AgentContext, AgentResult
from backend.config import CONFIG


class SecurityRAGAgent(BaseAgent):
    def __init__(self):
        super().__init__("security_rag")
        self.cache: Dict[str, Any] = {}
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict[str, List[str]]:
        kb = {}
        kb_dir = Path("backend/rag_agent/knowledge")
        if kb_dir.exists():
            for f in kb_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    kb[f.stem] = data
                except Exception:
                    pass
        return kb

    def _semantic_search(self, query: str, source: str, top_k: int = 5) -> List[Dict]:
        results = []
        entries = self.knowledge_base.get(source, [])
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        for entry in entries:
            if isinstance(entry, str):
                text = entry
                metadata = {}
            elif isinstance(entry, dict):
                text = entry.get("text", entry.get("content", json.dumps(entry)))
                metadata = {k: v for k, v in entry.items() if k not in ("text", "content")}
            else:
                continue

            text_lower = text.lower()
            text_tokens = set(text_lower.split())
            overlap = len(query_tokens & text_tokens)
            score = overlap / max(len(query_tokens), 1) if query_tokens else 0

            if score > 0:
                results.append({
                    "text": text[:500],
                    "score": round(score, 4),
                    "source": source,
                    "metadata": metadata,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    async def execute(self, context: AgentContext) -> AgentResult:
        query = context.query
        cache_key = hashlib.md5(query.encode()).hexdigest()

        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached["timestamp"] < CONFIG.rag.cache_ttl_s:
                cached["source"] = "cache"
                return AgentResult(
                    agent_name=self.name,
                    success=True,
                    output=cached,
                    confidence=0.99,
                )

        all_results = []
        for source in CONFIG.rag.sources:
            results = self._semantic_search(query, source, top_k=CONFIG.rag.top_k)
            all_results.extend(results)

        all_results.sort(key=lambda x: x["score"], reverse=True)
        reranked = all_results[:CONFIG.rag.rerank_top_k]

        context_passages = [r["text"] for r in reranked]

        if not context_passages:
            context_passages = [
                "Aucun contexte specifique trouve dans la base de connaissances.",
                "Utiliser les capacites generatives des modeles LLM pour repondre.",
            ]

        output = {
            "passages": context_passages,
            "sources": list(set(r["source"] for r in reranked)),
            "total_results": len(all_results),
            "reranked_count": len(reranked),
            "top_scores": [r["score"] for r in reranked],
            "source": "kb_search",
        }

        self.cache[cache_key] = {**output, "timestamp": time.time()}

        confidence = min(0.5 + 0.1 * len(reranked), 0.95)
        return AgentResult(
            agent_name=self.name,
            success=True,
            output=output,
            confidence=confidence,
            metadata={"sources_found": len(all_results), "kb_entries": {k: len(v) for k, v in self.knowledge_base.items()}},
        )
