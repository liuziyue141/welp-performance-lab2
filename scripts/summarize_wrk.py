"""Extract trial metrics from this repository's customized wrk2 output."""
import argparse
import csv
import json
import re
from pathlib import Path

FIELDS = ["run", "distribution", "configured_rate_rps", "frontend_replicas", "trial",
          "duration", "sent_rps", "completed_rps", "p99_ms", "mean_ms",
          "completed_requests", "non_2xx_3xx", "connect_errors", "read_errors",
          "write_errors", "timeouts", "exit_status"]


def milliseconds(value, unit):
    return float(value) * {"us": 0.001, "ms": 1, "s": 1000, "m": 60000}[unit]


def parse_output(text):
    metrics = {}
    for key, label in [("sent_rps", "Sent Requests/sec (Load)"),
                       ("completed_rps", "Completed Requests/sec (Throughput)")]:
        match = re.search(re.escape(label) + r":\s*([\d.]+)", text)
        if match:
            metrics[key] = float(match[1])
    match = re.search(r"^\s*99\.000%\s+([\d.]+)(us|ms|s|m)\b", text, re.M)
    if match:
        metrics["p99_ms"] = milliseconds(*match.groups())
    match = re.search(r"^\s*Latency\s+([\d.]+)(us|ms|s|m)\b", text, re.M)
    if match:
        metrics["mean_ms"] = milliseconds(*match.groups())
    match = re.search(r"(\d+) completed requests in", text)
    if match:
        metrics["completed_requests"] = int(match[1])
    match = re.search(r"Non-2xx or 3xx responses:\s*(\d+)", text)
    metrics["non_2xx_3xx"] = int(match[1]) if match else 0
    match = re.search(r"Socket errors: connect (\d+), read (\d+), write (\d+), timeout (\d+)", text)
    if match:
        metrics.update(zip(["connect_errors", "read_errors", "write_errors", "timeouts"],
                           map(int, match.groups())))
    else:
        metrics.update(dict.fromkeys(["connect_errors", "read_errors", "write_errors", "timeouts"], 0))
    required = {"sent_rps", "completed_rps", "p99_ms", "mean_ms", "completed_requests"}
    if not required.issubset(metrics):
        raise ValueError("Incomplete wrk2 output: " + ", ".join(sorted(required - metrics.keys())))
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", type=Path, help="one run directory or a directory of runs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inputs = sorted(args.runs.rglob("wrk2.txt"))
    if not inputs:
        parser.error("No wrk2.txt files found")
    rows = []
    for path in inputs:
        metadata = json.loads((path.parent / "metadata.json").read_text())
        row = {key: metadata[key] for key in FIELDS if key in metadata}
        row.update(parse_output(path.read_text()))
        row["run"] = path.parent.name
        row["exit_status"] = (path.parent / "exit-status.txt").read_text().strip()
        rows.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
