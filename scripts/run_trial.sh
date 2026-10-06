#!/usr/bin/env bash
# A new collection helper documenting the course workflow; not a historical run script.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ $# -ne 5 ]]; then
  echo "usage: $0 {const|exp} RATE TRIAL DURATION FRONTEND_REPLICAS" >&2
  exit 2
fi
distribution=$1
rate=$2
trial=$3
duration=$4
replicas=$5
[[ "$distribution" == const || "$distribution" == exp ]] || exit 2
[[ "$rate" =~ ^[1-9][0-9]*$ && "$trial" =~ ^[1-9][0-9]*$ && "$replicas" =~ ^[1-9][0-9]*$ ]] || exit 2
[[ "$duration" =~ ^[1-9][0-9]*[smh]$ ]] || exit 2
namespace=${LAB2_NAMESPACE:-lab2}
endpoint=${LAB2_URL:-http://10.96.88.88:8080}
cores=${LAB2_LOAD_CORES:-0-2}
for required in kubectl taskset python3; do command -v "$required" >/dev/null; done
[[ -x ./wrk2/wrk ]] || { echo "Build wrk2 first" >&2; exit 1; }
actual=$(kubectl -n "$namespace" get deployment frontend -o jsonpath='{.status.readyReplicas}')
[[ "$actual" == "$replicas" ]] || { echo "Expected $replicas ready frontend replicas; found ${actual:-0}" >&2; exit 1; }
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="results/runs/${stamp}-${distribution}-r${rate}-n${replicas}-t${trial}"
mkdir -p results/runs
mkdir "$out"
logger_pids=()
cleanup() {
  for pid in "${logger_pids[@]}"; do kill "$pid" 2>/dev/null || true; done
  for pid in "${logger_pids[@]}"; do wait "$pid" 2>/dev/null || true; done
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
kubectl -n "$namespace" get pods -o wide > "$out/pods.txt"
kubectl -n "$namespace" get deployments frontend detail -o yaml > "$out/deployments.yaml"
kubectl -n "$namespace" get pods -l app=frontend -o name > "$out/frontend-pods.txt"
while IFS= read -r pod; do
  kubectl -n "$namespace" logs "$pod" --tail=0 -f > "$out/${pod#pod/}.log" 2> "$out/${pod#pod/}.log.stderr" &
  logger_pids+=("$!")
done < "$out/frontend-pods.txt"
python3 - "$out" "$distribution" "$rate" "$trial" "$duration" "$replicas" "$endpoint" "$cores" <<'PY'
import datetime, json, pathlib, sys
out, dist, rate, trial, duration, replicas, endpoint, cores = sys.argv[1:]
metadata = dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                distribution=dist, configured_rate_rps=int(rate), trial=int(trial),
                duration=duration, frontend_replicas=int(replicas), endpoint=endpoint,
                load_generator_cores=cores, threads=3, connections=90,
                workload="workloads/lab2/simple-detail.lua")
(pathlib.Path(out)/"metadata.json").write_text(json.dumps(metadata, indent=2)+"\n")
PY
command=(taskset -c "$cores" ./wrk2/wrk -D "$distribution" -t 3 -c 90 -d "$duration" -s ./workloads/lab2/simple-detail.lua "$endpoint" -R "$rate" -L)
printf '%q ' "${command[@]}" > "$out/command.txt"
printf '\n' >> "$out/command.txt"
set +e
"${command[@]}" 2>&1 | tee "$out/wrk2.txt"
status=${PIPESTATUS[0]}
set -e
printf '%s\n' "$status" > "$out/exit-status.txt"
cleanup
logger_pids=()
python3 scripts/summarize_wrk.py "$out" --output "$out/summary.csv"
echo "Artifacts saved in $out"
exit "$status"
