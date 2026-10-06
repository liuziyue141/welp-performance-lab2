"""Plot trial-averaged p99 with population SD bars from collected run summaries."""
import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--x", choices=["configured_rate_rps", "sent_rps", "completed_rps"],
                        default="configured_rate_rps")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    groups = defaultdict(lambda: defaultdict(list))
    with args.summary.open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["exit_status"] != "0":
                raise ValueError(f"Failed run {row['run']}; inspect it before plotting")
            key = (row["distribution"], int(row["frontend_replicas"]), row["duration"],
                   int(row["configured_rate_rps"]))
            groups[key[:3]][key[3]].append((float(row[args.x]), float(row["p99_ms"])))
    if not groups:
        raise ValueError("No trial rows to plot")
    fig, ax = plt.subplots(figsize=(10, 6))
    for (distribution, replicas, duration), rates in sorted(groups.items()):
        xs, ys, errors = [], [], []
        for rate, trials in sorted(rates.items()):
            if len(trials) < 5:
                print(f"Warning: {distribution}, {replicas} replicas, {rate} RPS has only {len(trials)} trials")
            xs.append(statistics.mean(x for x, _ in trials))
            ys.append(statistics.mean(y for _, y in trials))
            errors.append(statistics.pstdev(y for _, y in trials))
        ax.errorbar(xs, ys, yerr=errors, marker="o", capsize=4,
                    label=f"{distribution}, {replicas} frontend replica(s), {duration}")
    labels = {"configured_rate_rps": "Configured arrival rate (requests/s)",
              "sent_rps": "Measured sent rate (requests/s)",
              "completed_rps": "Measured completed throughput (requests/s)"}
    ax.set_xlabel(labels[args.x])
    ax.set_ylabel("Mean of trial p99 latency (ms)")
    ax.axhline(500, color="red", linestyle="--", label="500 ms tail-latency target")
    ax.set_title("Welp detail workload: mean trial p99 ± population SD")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)


if __name__ == "__main__":
    main()
