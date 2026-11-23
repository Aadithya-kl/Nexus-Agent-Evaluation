"""Verify a caller's synthetic declarations with an explicit evaluator path.

Run from any working directory. --output-dir must name a new directory.
This is a software integration demo, not an actual agent or adoption result.
"""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys


def run_demo(evaluator: Path, output: Path) -> dict:
    evaluator = evaluator.resolve(strict=True)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures = Path(__file__).resolve().parent
    for name in ("cases.json", "predictions.json", "rejected-predictions.json"):
        shutil.copyfile(fixtures / name, output / name)
    (output / "invalid-cases.json").write_text("{", encoding="utf-8")
    observations = []
    scenarios = (
        ("accepted", "cases.json", "predictions.json", 0),
        ("critical-rejected", "cases.json", "rejected-predictions.json", 1),
        ("invalid-input", "invalid-cases.json", "predictions.json", 2),
    )
    for label, cases, predictions, expected in scenarios:
        report_path = output / (label + ".report.json")
        process = subprocess.run(
            [sys.executable, str(evaluator), "--min-pass-rate=0", "--output=" + str(report_path),
             "--", cases, predictions], cwd=output, capture_output=True, timeout=30,
        )
        (output / (label + ".stdout.txt")).write_bytes(process.stdout)
        (output / (label + ".stderr.txt")).write_bytes(process.stderr)
        if process.returncode != expected:
            raise RuntimeError(f"{label}: expected exit {expected}, received {process.returncode}")
        if expected == 2:
            if report_path.exists() or process.stdout or not process.stderr:
                raise RuntimeError("invalid input must fail without a new report or stdout")
            accepted = None
        else:
            report = json.loads(process.stdout)
            if report != json.loads(report_path.read_text(encoding="utf-8")):
                raise RuntimeError(f"{label}: saved report differs from stdout")
            accepted = expected == 0
            if (report["accepted"] is not accepted or report["gate_passed"] is not accepted
                    or report["total"] != 2 or report["minimum_pass_rate"] != 0
                    or report["passed"] != (2 if accepted else 1)
                    or report["critical_failures"] != ([] if accepted else ["ticket-review-01"])
                    or report["unexpected_predictions"] != []):
                raise RuntimeError(f"{label}: unexpected acceptance semantics")
        observations.append({"scenario": label, "expected_exit": expected,
                             "observed_exit": process.returncode, "accepted": accepted})
    summary = {"scope": "maintainer synthetic consumer demo; no real agent or adoption claim",
               "python": platform.python_version(), "platform": platform.system(),
               "evaluator_sha256": hashlib.sha256(evaluator.read_bytes()).hexdigest(),
               "fixture_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                                  for name in ("cases.json", "predictions.json", "rejected-predictions.json")},
               "verified": True, "observations": observations}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evaluator", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = run_demo(args.evaluator, args.output_dir)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Demo failed: {exc}\n")
    print(json.dumps(summary, indent=2))
