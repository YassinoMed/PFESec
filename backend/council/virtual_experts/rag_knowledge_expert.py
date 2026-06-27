"""Expert 10 — RAG Knowledge Base Query Specialist.
Queries local MITRE ATT&CK, CVE, OWASP, and Sigma knowledge bases.
"""
import json
from pathlib import Path
from typing import Dict, List
from backend.council.virtual_experts.base import VirtualExpert

_KB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "backend" / "rag_agent" / "knowledge"


class RAGKnowledgeExpert(VirtualExpert):
    expert_id = "rag_knowledge_expert"
    expert_name = "Knowledge Base Analyst"
    category = "rag_knowledge"
    capabilities = ["mitre_knowledge", "cve_lookup", "owasp_reference", "sigma_knowledge", "security_frameworks"]
    MITRE_TECHNIQUES = ["T1592 - Gather Victim Host Information"]

    HIGH_CONF_KEYWORDS = [
        "mitre", "att&ck", "cve", "nvd", "cvss", "owasp", "sigma",
        "nist", "iso 27001", "pci dss", "gdpr", "nis2", "framework",
    ]
    MED_CONF_KEYWORDS = [
        "vulnerability", "exploit", "patch", "advisory", "standard",
        "guideline", "best practice", "regulation",
    ]

    def __init__(self):
        self._kb: List[Dict] = self._load_knowledge()

    def _load_knowledge(self) -> List[Dict]:
        entries = []
        if not _KB_DIR.exists():
            return entries
        for path in _KB_DIR.glob("*.json"):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, dict) and item.get("text"):
                            entries.append({"source": path.stem, "text": item["text"]})
            except Exception:
                continue
        return entries

    def _search_kb(self, query: str, top_k: int = 5) -> List[Dict]:
        import re
        query_words = set(re.findall(r"[a-z0-9_-]{3,}", query.lower()))
        scored = []
        for entry in self._kb:
            entry_words = set(re.findall(r"[a-z0-9_-]{3,}", entry["text"].lower()))
            overlap = len(query_words & entry_words)
            if overlap > 0:
                scored.append({**entry, "score": overlap / max(len(entry_words), 1)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        matches = self._search_kb(query)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "INFORMATIONAL"

        if matches:
            sources = list({m["source"] for m in matches})
            evidence.append(f"Base de connaissance interrogée: {', '.join(sources)}")
            for m in matches[:3]:
                evidence.append(f"[{m['source']}] {m['text'][:80]}...")
            confidence = min(confidence + len(matches) * 10, 90)

        if confidence >= 50:
            conclusion = "BLOCK"
            severity = "MEDIUM"
        elif confidence >= 25:
            conclusion = "UNKNOWN"
            severity = "LOW"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if matches:
            recs.append(f"Consulter la référence locale: {matches[0]['source']}")
        recs.append("Croiser avec les bases NIST NVD et MITRE ATT&CK en ligne")

        return {
            "response": f"KB Query: {len(matches)} référence(s) trouvée(s) dans {len({m['source'] for m in matches})} source(s).",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Connaissances limitées à la base locale — mise à jour recommandée"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
