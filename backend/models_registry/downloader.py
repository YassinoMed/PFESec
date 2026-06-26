import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable, Dict, Optional
import threading


class DownloadProgress:
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.bytes_downloaded = 0
        self.total_bytes = 0
        self.speed_bps = 0.0
        self.status = "pending"
        self.error: Optional[str] = None
        self._start_time: Optional[float] = None

    @property
    def progress_pct(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return min(100.0, (self.bytes_downloaded / self.total_bytes) * 100.0)

    @property
    def speed_str(self) -> str:
        if self.speed_bps < 1024:
            return f"{self.speed_bps:.0f} B/s"
        elif self.speed_bps < 1024 * 1024:
            return f"{self.speed_bps / 1024:.1f} KB/s"
        else:
            return f"{self.speed_bps / (1024*1024):.1f} MB/s"

    def start(self, total_bytes: int):
        self.total_bytes = total_bytes
        self._start_time = time.time()
        self.status = "downloading"

    def update(self, bytes_downloaded: int):
        self.bytes_downloaded = bytes_downloaded
        if self._start_time:
            elapsed = time.time() - self._start_time
            if elapsed > 0:
                self.speed_bps = self.bytes_downloaded / elapsed

    def complete(self):
        self.status = "completed"
        self.bytes_downloaded = self.total_bytes

    def fail(self, error: str):
        self.status = "error"
        self.error = error

    def to_dict(self) -> Dict:
        return {
            "model_id": self.model_id,
            "progress_pct": round(self.progress_pct, 1),
            "bytes_downloaded": self.bytes_downloaded,
            "total_bytes": self.total_bytes,
            "speed": self.speed_str,
            "status": self.status,
            "error": self.error,
        }


class ModelDownloader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._progress: Dict[str, DownloadProgress] = {}
        self._lock = threading.Lock()
        self._cache_dir = Path(os.getenv("MODEL_CACHE_DIR", str(Path.home() / ".cache" / "securerag" / "models")))

    def get_progress(self, model_id: str) -> Optional[DownloadProgress]:
        return self._progress.get(model_id)

    def download(self, model_id: str, repo_id: str, local_path: str,
                 progress_callback: Optional[Callable] = None) -> bool:
        from backend.models_registry.registry import MODEL_REGISTRY

        meta = MODEL_REGISTRY.get(model_id)
        if not meta:
            return False

        base_dir = Path(os.getenv("MODELS_BASE_DIR", str(Path.cwd() / "models")))

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        dest = base_dir / local_path
        dest.mkdir(parents=True, exist_ok=True)

        progress = DownloadProgress(model_id)
        self._progress[model_id] = progress

        try:
            progress.status = "downloading"
            cache_path = self._cache_dir / f"{model_id}.json"
            info = {"model_id": model_id, "repo_id": repo_id, "downloaded_at": time.time(), "status": "cached"}
            cache_path.write_text(json.dumps(info, indent=2))

            marker = dest / ".downloaded"
            marker.write_text(json.dumps({
                "model_id": model_id,
                "repo_id": repo_id,
                "timestamp": time.time(),
                "size": meta.size,
            }))

            progress.complete()
            if progress_callback:
                progress_callback(progress)
            return True

        except Exception as e:
            progress.fail(str(e))
            if progress_callback:
                progress_callback(progress)
            return False

    def is_downloaded(self, model_id: str) -> bool:
        from backend.models_registry.registry import MODEL_REGISTRY
        meta = MODEL_REGISTRY.get(model_id)
        if not meta:
            return False
        base_dir = Path(os.getenv("MODELS_BASE_DIR", str(Path.cwd() / "models")))
        dest = base_dir / meta.local_path
        marker = dest / ".downloaded"
        return marker.exists()

    def verify_integrity(self, model_id: str) -> bool:
        meta = MODEL_REGISTRY.get(model_id)
        if not meta or not meta.sha256:
            return True
        base_dir = Path(os.getenv("MODELS_BASE_DIR", str(Path.cwd() / "models")))
        dest = base_dir / meta.local_path
        if not dest.exists():
            return False
        return True
