"""Tests for Benchmark v1 (F28) — pure unit, no DB."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from eval.benchmark import (
    BenchmarkCase,
    load_benchmark,
    compute_metrics,
    PredictionResult,
)


def _make_sample_benchmark() -> list[dict]:
    """Create sample benchmark data for testing."""
    return [
        {"id": "BM-0000", "text": "test text about arrest", "expected_fraud_type": "digital_arrest",
         "expected_risk": "danger", "district": "mumbai", "language": "hi"},
        {"id": "BM-0001", "text": "test text about investment", "expected_fraud_type": "investment_fraud",
         "expected_risk": "danger", "district": "delhi", "language": "en"},
        {"id": "BM-0002", "text": "test text about job", "expected_fraud_type": "job_fraud",
         "expected_risk": "suspicious", "district": "bangalore", "language": "en"},
    ]


class TestLoadBenchmark:
    def test_loads_from_json_array(self) -> None:
        data = _make_sample_benchmark()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fpath = Path(f.name)

        try:
            cases = load_benchmark(fpath)
            assert len(cases) == 3
            assert all(isinstance(c, BenchmarkCase) for c in cases)
            assert cases[0].expected_fraud_type == "digital_arrest"
        finally:
            fpath.unlink()

    def test_loads_from_dict_with_cases_key(self) -> None:
        data = {"cases": _make_sample_benchmark()}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fpath = Path(f.name)

        try:
            cases = load_benchmark(fpath)
            assert len(cases) == 3
        finally:
            fpath.unlink()

    def test_handles_empty_array(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            fpath = Path(f.name)

        try:
            # Should exit with sys.exit(1)
            import sys
            original_exit = sys.exit
            exit_called = False
            def mock_exit(code=0):
                nonlocal exit_called
                exit_called = True
                raise SystemExit(code)
            sys.exit = mock_exit

            try:
                load_benchmark(fpath)
            except SystemExit:
                pass
            finally:
                sys.exit = original_exit

            assert exit_called, "Should exit on empty benchmark"
        finally:
            fpath.unlink()


class TestComputeMetrics:
    def test_perfect_predictions(self) -> None:
        results = [
            PredictionResult("1", "digital_arrest", "digital_arrest", "danger", "danger",
                             0.9, False, True, True),
            PredictionResult("2", "investment_fraud", "investment_fraud", "danger", "danger",
                             0.85, False, True, True),
            PredictionResult("3", "job_fraud", "job_fraud", "suspicious", "suspicious",
                             0.75, False, True, True),
        ]
        summary = compute_metrics(results)
        assert summary.accuracy == 1.0
        assert summary.precision_macro == 1.0
        assert summary.recall_macro == 1.0
        assert summary.fp_rate == 0.0
        assert summary.num_degraded == 0

    def test_all_wrong_predictions(self) -> None:
        results = [
            PredictionResult("1", "digital_arrest", "investment_fraud", "danger", "unknown",
                             0.3, True, False, False),
            PredictionResult("2", "investment_fraud", "digital_arrest", "danger", "suspicious",
                             0.4, True, False, False),
        ]
        summary = compute_metrics(results)
        assert summary.accuracy == 0.0
        assert summary.num_degraded == 2

    def test_mixed_results(self) -> None:
        results = [
            PredictionResult("1", "digital_arrest", "digital_arrest", "danger", "danger",
                             0.9, False, True, True),
            PredictionResult("2", "digital_arrest", "digital_arrest", "danger", "suspicious",
                             0.7, False, True, False),
            PredictionResult("3", "investment_fraud", "digital_arrest", "danger", "unknown",
                             0.5, True, False, False),
            PredictionResult("4", "job_fraud", "job_fraud", "suspicious", "suspicious",
                             0.8, False, True, True),
        ]
        summary = compute_metrics(results)
        assert summary.total_cases == 4
        assert summary.accuracy == 0.75  # 3/4 correct
        assert summary.num_degraded == 1

    def test_handles_empty_results(self) -> None:
        summary = compute_metrics([])
        assert summary.total_cases == 0
        assert summary.accuracy == 0.0

    def test_computes_per_type_metrics(self) -> None:
        results = [
            PredictionResult("1", "digital_arrest", "digital_arrest", "danger", "danger",
                             0.9, False, True, True),
            PredictionResult("2", "digital_arrest", "digital_arrest", "danger", "danger",
                             0.8, False, True, True),
            PredictionResult("3", "digital_arrest", "investment_fraud", "danger", "unknown",
                             0.4, False, False, False),
        ]
        summary = compute_metrics(results)
        assert "digital_arrest" in summary.per_type
        da = summary.per_type["digital_arrest"]
        assert da["tp"] == 2
        assert da["fn"] == 1
        assert da["support"] == 3
