"""Tests pour l'Evidence Fusion"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.fusion.evidence_fusion import EvidenceFuser


def test_fuse_classifications():
    fuser = EvidenceFuser()
    results = [
        {"model_id": "cysecbert", "verdict": "BLOCK", "confidence": 0.95},
        {"model_id": "phishsense", "verdict": "ACCEPT", "confidence": 0.60},
    ]
    fused = fuser.fuse_classifications(results)
    assert fused["verdict"] == "BLOCK"
    assert fused["confidence"] > 0.5
    print(f"[PASS] Fusion verdict={fused['verdict']}, conf={fused['confidence']}")


def test_fuse_classifications_tie():
    fuser = EvidenceFuser()
    results = [
        {"model_id": "cysecbert", "verdict": "BLOCK", "confidence": 0.5},
        {"model_id": "phishsense", "verdict": "ACCEPT", "confidence": 0.5},
    ]
    fused = fuser.fuse_classifications(results)
    print(f"[PASS] Fusion tie: verdict={fused['verdict']}, block={fused['block_weight']}, accept={fused['accept_weight']}")


def test_fuse_classifications_empty():
    fuser = EvidenceFuser()
    fused = fuser.fuse_classifications([])
    assert fused["verdict"] == "UNKNOWN"
    print(f"[PASS] Fusion empty: verdict={fused['verdict']}")


def test_threat_score():
    fuser = EvidenceFuser()
    model_results = [
        {"model_id": "cysecbert", "threat_score": 85},
        {"model_id": "phishsense", "threat_score": 75},
    ]
    agent_results = []
    score = fuser.compute_threat_score(model_results, agent_results)
    assert score > 0
    print(f"[PASS] Threat score={score}")


if __name__ == "__main__":
    test_fuse_classifications()
    test_fuse_classifications_tie()
    test_fuse_classifications_empty()
    test_threat_score()
    print("\n[OK] Tous les tests fusion passes!")
