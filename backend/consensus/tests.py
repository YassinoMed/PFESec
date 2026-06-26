import time
from typing import List
from backend.consensus.engine import ConsensusEngine, ModelVote, ConsensusResult
from backend.consensus.config import ConsensusConfig


def make_vote(model_id: str, confidence: float, response: str = None,
              inference_ms: float = 10.0, error: str = None) -> ModelVote:
    return ModelVote(
        model_id=model_id,
        model_name=model_id.replace("_", " ").title(),
        category="test",
        confidence=confidence,
        weight=1,
        response=response or f"Response from {model_id}",
        inference_ms=inference_ms,
        error=error,
    )


def test_all_high_confidence():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 95.0, "PHISHING"),
        make_vote("model_b", 93.0, "PHISHING"),
        make_vote("model_c", 91.0, "PHISHING"),
    ]
    result = engine.compute("test query", votes)
    assert result.global_score >= 90.0, f"Score {result.global_score} should be >= 90"
    assert result.consensus_reached == True, "Consensus should be reached"
    assert result.confidence_level == "High"
    assert result.total_retained == 3
    assert result.total_rejected == 0
    print(f"  PASS: all_high_confidence -> score={result.global_score:.1f}, consensus={result.consensus_reached}, level={result.confidence_level}")


def test_mixed_confidence():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 95.0, "PHISHING"),
        make_vote("model_b", 85.0, "PHISHING"),
        make_vote("model_c", 82.0, "SAFE"),
    ]
    result = engine.compute("test query", votes)
    assert result.total_retained == 3
    a_weight = [v for v in result.retained if v.model_id == "model_a"][0].weight
    b_weight = [v for v in result.retained if v.model_id == "model_b"][0].weight
    assert a_weight == 4, f"model_a weight should be 4, got {a_weight}"
    assert b_weight == 2, f"model_b weight should be 2, got {b_weight}"
    expected_score = (95.0 * 4 + 85.0 * 2 + 82.0 * 2) / (4 + 2 + 2)
    assert abs(result.global_score - expected_score) < 0.01, f"Score {result.global_score} != {expected_score}"
    print(f"  PASS: mixed_confidence -> score={result.global_score:.1f}, weights: a={a_weight}, b={b_weight}, c=2")


def test_single_above_threshold():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 92.0, "MALWARE"),
        make_vote("model_b", 45.0, "SAFE"),
        make_vote("model_c", 30.0, "SAFE"),
    ]
    result = engine.compute("test query", votes)
    assert result.total_retained == 1
    assert result.total_rejected == 2
    assert result.primary_model.model_id == "model_a"
    assert result.confidence_level == "High"
    print(f"  PASS: single_above_threshold -> retained={result.total_retained}, primary={result.primary_model.model_id}")


def test_none_above_threshold():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 65.0, "PHISHING"),
        make_vote("model_b", 55.0, "SAFE"),
        make_vote("model_c", 45.0, "PHISHING"),
    ]
    result = engine.compute("test query", votes)
    assert result.total_retained > 0
    assert result.global_score < 80.0, f"Score {result.global_score} should be < 80"
    assert result.consensus_reached == False
    assert result.warning is not None
    print(f"  PASS: none_above_threshold -> warning present, best={result.primary_model.model_id if result.primary_model else 'none'}, score={result.global_score:.1f}")


def test_timeout():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 95.0, "PHISHING"),
        make_vote("model_b", 0, error="Timeout"),
        make_vote("model_c", 92.0, "PHISHING"),
    ]
    result = engine.compute("test query", votes)
    assert result.total_retained == 2
    assert result.total_rejected == 1
    assert result.primary_model.model_id == "model_a"
    assert result.rejected[0].model_id == "model_b"
    assert result.rejected[0].error == "Timeout"
    print(f"  PASS: timeout -> retained={result.total_retained}, rejected={result.total_rejected}")


def test_contradictory_responses():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 95.0, "PHISHING"),
        make_vote("model_b", 94.0, "SAFE"),
    ]
    result = engine.compute("test query", votes)
    assert result.total_retained == 2
    assert result.global_score > 90.0
    print(f"  PASS: contradictory -> consensus={result.consensus_reached}, primary={result.primary_model.model_id}, score={result.global_score:.1f}")


def test_identical_responses():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 96.0, "PHISHING"),
        make_vote("model_b", 95.0, "PHISHING"),
        make_vote("model_c", 94.0, "PHISHING"),
    ]
    result = engine.compute("test query", votes)
    assert result.consensus_reached == True
    assert result.global_score >= 90.0
    assert result.final_response == "PHISHING" or (isinstance(result.final_response, dict) and "PHISHING" in str(result.final_response))
    print(f"  PASS: identical_responses -> consensus={result.consensus_reached}, score={result.global_score:.1f}")


def test_contributions_sum():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 95.0, "PHISHING"),
        make_vote("model_b", 88.0, "PHISHING"),
        make_vote("model_c", 75.0, "SAFE"),
    ]
    result = engine.compute("test query", votes)
    total_contrib = sum(result.contributions.values())
    assert abs(total_contrib - 100.0) < 0.01, f"Contributions sum to {total_contrib}, expected 100"
    print(f"  PASS: contributions_sum -> total={total_contrib:.1f}%")


def test_ranking_order():
    engine = ConsensusEngine()
    votes = [
        make_vote("model_a", 82.0, "B"),
        make_vote("model_b", 95.0, "A"),
        make_vote("model_c", 88.0, "C"),
    ]
    result = engine.compute("test query", votes)
    ranking = result.to_dict()["ranking"]
    scores = [r["confidence"] for r in ranking]
    assert scores == sorted(scores, reverse=True), f"Ranking not sorted: {scores}"
    print(f"  PASS: ranking_order -> scores={scores}")


if __name__ == "__main__":
    print("\n=== Consensus Engine Tests ===\n")
    tests = [
        test_all_high_confidence,
        test_mixed_confidence,
        test_single_above_threshold,
        test_none_above_threshold,
        test_timeout,
        test_contradictory_responses,
        test_identical_responses,
        test_contributions_sum,
        test_ranking_order,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__} -> {e}")
        except Exception as e:
            print(f"  ERROR: {t.__name__} -> {e}")

    print(f"\n=== {passed}/{len(tests)} tests passed ===\n")
