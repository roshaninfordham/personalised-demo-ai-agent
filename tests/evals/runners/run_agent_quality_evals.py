from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--category", default="all")
    parser.add_argument("--provider", default="fake")
    parser.add_argument("--max-cases", type=int, default=0)
    parser.add_argument("--output", default="tests/evals/reports/eval_report.json")
    parser.add_argument("--junit-output", default="tests/evals/reports/eval_report.xml")
    args = parser.parse_args()

    cases = list(_load_cases(Path(args.dataset), args.category))
    if args.max_cases > 0:
        cases = cases[: args.max_cases]
    report = run_cases(cases, provider=str(args.provider))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    junit = Path(args.junit_output)
    junit.parent.mkdir(parents=True, exist_ok=True)
    junit.write_text(_junit_xml(report))
    return 0 if report["summary"]["failed"] == 0 else 1


def run_cases(cases: list[dict[str, Any]], *, provider: str) -> dict[str, Any]:
    started_at = datetime.now(UTC)
    scored_cases: list[dict[str, Any]] = []
    for case in cases:
        scored = _score_case(case)
        scored_cases.append({**case, "score": scored, "passed": bool(scored["passed"])})
    completed_at = datetime.now(UTC)
    passed = sum(1 for case in scored_cases if case["passed"])
    failed = len(scored_cases) - passed
    grounding_scores = [
        float(case["score"].get("grounding_score", 1.0))
        for case in scored_cases
        if isinstance(case["score"], Mapping)
    ]
    recipe_scores = [
        float(case["score"].get("recipe_completion_score", 1.0))
        for case in scored_cases
        if isinstance(case["score"], Mapping)
    ]
    recovery_scores = [
        float(case["score"].get("recovery_success", 1.0))
        for case in scored_cases
        if isinstance(case["score"], Mapping)
    ]
    summary = {
        "total": len(scored_cases),
        "passed": passed,
        "failed": failed,
        "grounding_score_avg": _average(grounding_scores),
        "recipe_completion_score_avg": _average(recipe_scores),
        "recovery_success_rate": _average(recovery_scores),
        "safety_violations": sum(
            int(case["score"].get("safety_violations", 0)) for case in scored_cases
        ),
        "hallucination_count": sum(
            int(case["score"].get("hallucination_count", 0)) for case in scored_cases
        ),
    }
    return {
        "run_id": str(uuid4()),
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "provider": provider,
        "summary": summary,
        "cases": scored_cases,
    }


def _score_case(case: Mapping[str, Any]) -> dict[str, float | int | bool]:
    category = str(case.get("category") or "")
    if category == "grounded_answers":
        from tests.evals.scorers.grounding_scorer import score_grounding

        return score_grounding(case)
    if category == "hallucination_avoidance":
        from tests.evals.scorers.hallucination_scorer import score_hallucination

        return dict(score_hallucination(case))
    if category == "recipe_completion":
        from tests.evals.scorers.recipe_completion_scorer import score_recipe_completion

        return score_recipe_completion(case)
    if category == "recovery_behavior":
        from tests.evals.scorers.recovery_scorer import score_recovery

        return score_recovery(case)
    if category == "safety_compliance":
        from tests.evals.scorers.safety_scorer import score_safety

        return dict(score_safety(case))
    return {"passed": False}


def _load_cases(dataset: Path, category: str) -> Iterable[dict[str, Any]]:
    files = sorted(dataset.glob("*.jsonl")) if dataset.is_dir() else [dataset]
    for file_path in files:
        for line_number, line in enumerate(file_path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            parsed = json.loads(line)
            if not isinstance(parsed, dict):
                raise ValueError(f"{file_path}:{line_number} must contain a JSON object")
            if category != "all" and parsed.get("category") != category:
                continue
            yield parsed


def _average(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 1.0


def _junit_xml(report: Mapping[str, Any]) -> str:
    cases = report.get("cases")
    case_list = cases if isinstance(cases, list) else []
    suite = ElementTree.Element(
        "testsuite",
        {
            "name": "agent-quality-evals",
            "tests": str(len(case_list)),
            "failures": str(sum(1 for case in case_list if not bool(case.get("passed")))),
        },
    )
    for case in case_list:
        item = ElementTree.SubElement(
            suite,
            "testcase",
            {"classname": str(case.get("category")), "name": str(case.get("eval_id"))},
        )
        if not bool(case.get("passed")):
            failure = ElementTree.SubElement(item, "failure", {"message": "eval failed"})
            failure.text = json.dumps(case.get("score"), sort_keys=True)
    return ElementTree.tostring(suite, encoding="unicode")


if __name__ == "__main__":
    sys.exit(main())
