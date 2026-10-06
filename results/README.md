# Experiment data

`report-summary.csv` transcribes the eight numerical latency points stated on page 1 of [the original report](../reports/lab2-analysis.pdf). It is an aggregate reference table, not raw data. The figures identify p99 latency, while the prose sometimes calls these values average latency; the original labels are discussed in [the write-up](../docs/writeup.md).

The original five-trial measurements, full rate sweeps, pod logs, and optimization source are not present in the supplied checkout. They cannot be recovered from this CSV. The reported load values do not establish measured sent or completed rates.

`runs/` is ignored by Git. If the collection helper is used on a provisioned VM, each new run contains:

```text
<timestamp>-<distribution>-r<rate>-n<replicas>-t<trial>/
  metadata.json          # Requested experiment configuration
  command.txt            # Exact load-generator invocation
  wrk2.txt               # Complete stdout/stderr
  exit-status.txt        # Load-generator process exit status
  pods.txt               # Pod placement snapshot
  deployments.yaml       # Resource and replica configuration
  frontend-pods.txt       # Pods selected for log capture
  <frontend-pod>.log      # Streamed client-side RPC timing records
  <frontend-pod>.log.stderr
  summary.csv            # Parsed trial metrics
```

Run summaries retain errors and timeouts. Completed HTTP responses can include failed operations, and a zero process exit status is not proof of a successful benchmark. Review both `wrk2.txt` and captured logger errors before aggregating runs.
