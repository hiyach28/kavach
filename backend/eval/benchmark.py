#!/usr/bin/env python3
"""F28: KAVACH Benchmark v1 — eval harness.

Measures classification quality against a labeled benchmark set.

Usage:
    python -m eval.benchmark                                          # uses benchmark_cases.json
    python -m eval.benchmark --benchmark data/synthetic/manifest.json # ground truth from F27
    python -m eval.benchmark --verbose                                # detailed per-case output

Output:
    Writes evaluation results to data/benchmark/eval_runs.jsonl and prints a summary table.

Metrics:
    - Precision  (per fraud type + macro avg)
    - Recall     (per fraud type + macro avg)
    - F1-Score   (per fraud type + macro avg)
    - FP Rate    (false positives per total predicted)
    - Accuracy   (overall correct)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Ensure backend/ is on path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.llm_client import classify  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("benchmark")

_DATA_DIR = BACKEND_DIR.parent / "data"
_BENCHMARK_FILE = _DATA_DIR / "benchmark" / "benchmark_cases.json"
_EVAL_RUNS_FILE = _DATA_DIR / "benchmark" / "eval_runs.jsonl"


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class BenchmarkCase:
    """A single labeled test case."""
    id: str
    text: str
    expected_fraud_type: str
    expected_risk: str
    district: str = ""
    language: str = "hi"


@dataclass
class PredictionResult:
    text_id: str
    expected_fraud_type: str
    predicted_fraud_type: str
    expected_risk: str
    predicted_risk: str
    confidence: float
    degraded: bool
    correct_fraud_type: bool
    correct_risk: bool


@dataclass
class EvalMetrics:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvalSummary:
    timestamp: str
    total_cases: int
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    fp_rate: float
    per_type: dict[str, dict[str, float]]
    num_degraded: int
    benchmark_file: str = ""


# ── Load benchmark ─────────────────────────────────────────────────────────────

def load_benchmark(path: Path | None = None) -> list[BenchmarkCase]:
    """Load labeled benchmark cases from a JSON file."""
    filepath = path or _BENCHMARK_FILE
    if not filepath.exists():
        logger.error("Benchmark file not found: %s", filepath)
        logger.error("Run 'make seed-demo' first or specify --benchmark path")
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    # Support both raw list and {"cases": [...]} format
    if isinstance(data, dict) and "cases" in data:
        data = data["cases"]

    cases: list[BenchmarkCase] = []
    for item in data:
        cases.append(BenchmarkCase(
            id=item.get("id", str(len(cases))),
            text=item.get("text", ""),
            expected_fraud_type=item.get("expected_fraud_type", item.get("fraud_type", "other")),
            expected_risk=item.get("expected_risk", item.get("risk", "unknown")),
            district=item.get("district", ""),
            language=item.get("language", "hi"),
        ))

    if not cases:
        logger.error("No benchmark cases found in %s", filepath)
        sys.exit(1)

    logger.info("Loaded %d benchmark cases from %s", len(cases), filepath)
    return cases


# ── Run inference ──────────────────────────────────────────────────────────────

def predict(cases: list[BenchmarkCase]) -> list[PredictionResult]:
    """Run the classification pipeline on all benchmark cases."""
    results: list[PredictionResult] = []

    for i, case in enumerate(cases):
        try:
            verdict = classify(case.text)

            results.append(PredictionResult(
                text_id=case.id,
                expected_fraud_type=case.expected_fraud_type,
                predicted_fraud_type=verdict.fraud_type.value,
                expected_risk=case.expected_risk,
                predicted_risk=verdict.risk.value,
                confidence=verdict.confidence,
                degraded=verdict.degraded,
                correct_fraud_type=verdict.fraud_type.value == case.expected_fraud_type,
                correct_risk=verdict.risk.value == case.expected_risk,
            ))
        except Exception as exc:
            logger.error("Error classifying case %s: %s", case.id, exc)
            results.append(PredictionResult(
                text_id=case.id,
                expected_fraud_type=case.expected_fraud_type,
                predicted_fraud_type="error",
                expected_risk=case.expected_risk,
                predicted_risk="error",
                confidence=0.0,
                degraded=True,
                correct_fraud_type=False,
                correct_risk=False,
            ))

        if (i + 1) % 50 == 0:
            logger.info("  Classified %d/%d cases", i + 1, len(cases))

    return results


# ── Compute metrics ────────────────────────────────────────────────────────────

def compute_metrics(results: list[PredictionResult]) -> EvalSummary:
    """Compute precision, recall, F1 per fraud type and macro averages."""
    total = len(results)
    if total == 0:
        return EvalSummary(
            timestamp=datetime.now(UTC).isoformat(),
            total_cases=0, accuracy=0.0,
            precision_macro=0.0, recall_macro=0.0, f1_macro=0.0,
            fp_rate=0.0, per_type={}, num_degraded=0,
        )

    correct_fraud = sum(1 for r in results if r.correct_fraud_type)
    correct_risk = sum(1 for r in results if r.correct_risk)
    accuracy = round(correct_fraud / total, 4)
    num_degraded = sum(1 for r in results if r.degraded)

    # Per-type metrics
    fraud_types = sorted(set(r.expected_fraud_type for r in results))
    per_type: dict[str, dict[str, float]] = {}

    for ft in fraud_types:
        tp = sum(1 for r in results if r.expected_fraud_type == ft and r.correct_fraud_type)
        fp = sum(1 for r in results if r.expected_fraud_type != ft and r.predicted_fraud_type == ft)
        fn = sum(1 for r in results if r.expected_fraud_type == ft and not r.correct_fraud_type)
        support = sum(1 for r in results if r.expected_fraud_type == ft)

        precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

        per_type[ft] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
            "tp": tp,
            "fp": fp,
            "fn": fn,
        }

    # Macro averages
    precision_macro = round(
        sum(v["precision"] for v in per_type.values()) / len(per_type), 4
    ) if per_type else 0.0
    recall_macro = round(
        sum(v["recall"] for v in per_type.values()) / len(per_type), 4
    ) if per_type else 0.0

    f1_numerator = sum(v["f1"] for v in per_type.values())
    f1_macro = round(f1_numerator / len(per_type), 4) if per_type else 0.0

    # FP rate = total false positives / total predicted positive
    total_fp = sum(v["fp"] for v in per_type.values())
    total_predicted_positive = sum(
        1 for r in results if r.predicted_fraud_type != "error"
    )
    fp_rate = round(total_fp / total_predicted_positive, 4) if total_predicted_positive > 0 else 0.0

    return EvalSummary(
        timestamp=datetime.now(UTC).isoformat(),
        total_cases=total,
        accuracy=accuracy,
        precision_macro=precision_macro,
        recall_macro=recall_macro,
        f1_macro=f1_macro,
        fp_rate=fp_rate,
        per_type=per_type,
        num_degraded=num_degraded,
    )


# ── Output ─────────────────────────────────────────────────────────────────────

def print_summary(summary: EvalSummary) -> None:
    """Print a human-readable evaluation summary."""
    print()
    print("=" * 60)
    print("KAVACH Benchmark v1 — Evaluation Summary")
    print("=" * 60)
    print(f"  Total cases:    {summary.total_cases}")
    print(f"  Accuracy:       {summary.accuracy:.2%}")
    print(f"  Precision (macro): {summary.precision_macro:.2%}")
    print(f"  Recall (macro):    {summary.recall_macro:.2%}")
    print(f"  F1 (macro):        {summary.f1_macro:.2%}")
    print(f"  FP rate:        {summary.fp_rate:.2%}")
    print(f"  Degraded predictions: {summary.num_degraded}/{summary.total_cases}")
    print()

    if summary.per_type:
        print(f"{'Fraud Type':<25} {'Precision':<10} {'Recall':<10} {'F1':<10} {'Support':<10}")
        print("-" * 65)
        for ft, metrics in sorted(summary.per_type.items()):
            print(f"{ft:<25} {metrics['precision']:<10.2%} {metrics['recall']:<10.2%} "
                  f"{metrics['f1']:<10.2%} {metrics['support']:<10}")
    print()


def save_run(summary: EvalSummary, run_path: Path = _EVAL_RUNS_FILE) -> None:
    """Append eval run to the runs file for tracking over time."""
    run_path.parent.mkdir(parents=True, exist_ok=True)
    with open(run_path, "a") as f:
        f.write(json.dumps(asdict(summary)) + "\n")
    logger.info("Eval run appended to %s", run_path)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="KAVACH Benchmark v1")
    parser.add_argument("--benchmark", type=str, default=None,
                        help="Path to benchmark JSON (default: data/benchmark/benchmark_cases.json)")
    parser.add_argument("--verbose", action="store_true",
                        help="Print per-case predictions")
    parser.add_argument("--save", action="store_true", default=True,
                        help="Save results to eval_runs.jsonl (default: True)")
    args = parser.parse_args()

    # 1. Load
    bench_path = Path(args.benchmark) if args.benchmark else None
    cases = load_benchmark(bench_path)

    # 2. Predict
    logger.info("Running classification on %d cases (mode: %s)...", len(cases), "mock")
    results = predict(cases)

    # 3. Evaluate
    summary = compute_metrics(results)

    # 4. Print
    print_summary(summary)

    if args.verbose:
        print("Per-case details:")
        print(f"{'ID':<10} {'Expected':<20} {'Predicted':<20} {'Conf':<8} {'Correct':<8}")
        print("-" * 70)
        for r in results:
            print(f"{r.text_id:<10} {r.expected_fraud_type:<20} {r.predicted_fraud_type:<20} "
                  f"{r.confidence:<8.2f} {'✓' if r.correct_fraud_type else '✗':<8}")

    # 5. Save
    if args.save:
        summary.benchmark_file = str(bench_path or _BENCHMARK_FILE)
        save_run(summary)

    # Exit code: 0 if accuracy >= 0.5, otherwise 1
    if summary.accuracy < 0.5:
        logger.warning("Accuracy below 50%% threshold (%.2f%%).", summary.accuracy * 100)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
