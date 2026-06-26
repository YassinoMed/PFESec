import json
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class VectorStore:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path) if path else Path("backend/rag_agent/vector_store")
        self.path.mkdir(parents=True, exist_ok=True)
        self.vectors: Dict[str, np.ndarray] = {}
        self.metadata: Dict[str, Dict] = {}
        self.index_path = self.path / "index.json"
        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            try:
                data = json.loads(self.index_path.read_text(encoding="utf-8"))
                for key, meta in data.items():
                    vec_path = self.path / f"{key}.npy"
                    if vec_path.exists():
                        self.vectors[key] = np.load(str(vec_path))
                        self.metadata[key] = meta
            except Exception:
                pass

    def _save_index(self):
        index = {}
        for key, meta in self.metadata.items():
            meta_clean = {k: v for k, v in meta.items() if k != "vector"}
            index[key] = meta_clean
            vec_path = self.path / f"{key}.npy"
            np.save(str(vec_path), self.vectors[key])
        self.index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, key: str, vector: np.ndarray, metadata: Optional[Dict] = None):
        self.vectors[key] = vector
        self.metadata[key] = metadata or {}
        self._save_index()

    def add_batch(self, keys: List[str], vectors: List[np.ndarray], metadatas: Optional[List[Dict]] = None):
        for i, key in enumerate(keys):
            self.vectors[key] = vectors[i]
            self.metadata[key] = (metadatas or [{}] * len(keys))[i]
        self._save_index()

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float, Dict]]:
        if not self.vectors:
            return []

        scores = []
        for key, vec in self.vectors.items():
            vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
            q_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)
            similarity = float(np.dot(vec_norm, q_norm))
            scores.append((key, similarity, self.metadata.get(key, {})))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def delete(self, key: str):
        self.vectors.pop(key, None)
        self.metadata.pop(key, None)
        vec_path = self.path / f"{key}.npy"
        if vec_path.exists():
            vec_path.unlink()
        self._save_index()

    def clear(self):
        self.vectors.clear()
        self.metadata.clear()
        for f in self.path.glob("*.npy"):
            f.unlink()
        if self.index_path.exists():
            self.index_path.unlink()

    @property
    def size(self) -> int:
        return len(self.vectors)

    def list_keys(self) -> List[str]:
        return list(self.vectors.keys())
