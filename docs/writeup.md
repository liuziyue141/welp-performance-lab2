# Lab 2 Performance Analysis and Queueing Theory

## Research questions

How does tail latency change as offered load increases? Do bursty arrivals cause overload sooner than evenly spaced arrivals? Which part of a microservice request path limits throughput, and how far can replication move that limit?

The team studied Welp, a restaurant application with an HTTP frontend and a gRPC detail service. The frontend translates requests into RPCs and encodes responses as JSON. The detail service reads and updates an in-memory restaurant map. Lab 2 exercises this path with approximately 80% `GetDetail` and 20% `PostDetail` requests.

The [original report](../reports/lab2-analysis.pdf), authored by Chris Kim, Jared Jose, and Ziyue Liu, contains the submitted figures and analysis. This write-up presents those results with explicit distinctions between offered load, measured throughput, and latency.

## Environment and measurements

The course setup specifies Kubernetes on a GCP Compute Engine VM. Its recommended environment is an `e2-standard-8` VM with 8 vCPUs and 32 GB RAM, Ubuntu 24.04 LTS, and a 20 GB boot disk. This describes the course configuration; the report does not record the actual machine inventory, installed versions, or every pod placement used for each run.

The experiment uses the course-customized `wrk2` generator. Constant arrivals use `-D const`, while exponential inter-arrival times use `-D exp`. The prescribed generator setup uses three threads, 90 connections, and Linux CPU affinity on logical CPUs 0–2. The course asks for at least five trials at each load and standard-deviation error bars.

Three rates must be distinguished:

- **Configured rate:** the requested arrival rate passed through `-R`.
- **Sent rate:** measured requests sent per second, printed as `Sent Requests/sec (Load)`.
- **Completed throughput:** completed responses per second, printed as `Completed Requests/sec (Throughput)`.

Completed responses can include HTTP errors. Sent rate can fall below configured rate if the generator is constrained. Raw outputs are needed to establish these distinctions for a historical point; the supplied report does not provide all of them.

The main response metric is p99 latency, with a 500 ms target. An average of trial p99 values is different from mean request latency and from the p99 of all pooled requests. The report figures label p99, but some prose uses “Avg latency.” The table below preserves the stated values without reconstructing unavailable request-level data.

## Experiment 1 Constant and exponential arrivals

The team increased the request rate from low load into overload, using finer increments near the region where latency rose sharply. The course procedure recommends doubling initial rates and then bisecting between underloaded and overloaded conditions.

| Arrival pattern | Reported load in requests/s | Reported latency in ms | Reported standard deviation in ms |
| --- | ---: | ---: | ---: |
| Constant | 9,000 | 28.92 | 28.11 |
| Constant | 9,400 | 139.22 | 33.09 |
| Constant | 10,800 | 2,160 | 448.37 |
| Constant | 12,800 | 13,060 | 1,971.04 |
| Exponential | 8,800 | 290.20 | 62.96 |
| Exponential | 9,400 | 933.57 | 152.88 |
| Exponential | 10,400 | 2,612 | 572.691 |
| Exponential | 12,800 | 10,632 | 2,468.50 |

Source: page 1 of the original report. These eight points are also available in [CSV form](../results/report-summary.csv); they do not constitute the full sweep or the five individual trials at each rate.

At 9,400 requests/s, exponential arrivals produced a much larger reported p99 latency than constant arrivals. The report estimates a 500 ms crossing near 9,300 requests/s for exponential arrivals and near 9,800 requests/s for constant arrivals. These are approximate boundaries from the report, rather than exact capacity measurements supported by the available CSV.

The queueing interpretation is that random short bursts can temporarily exceed service capacity even when the long-run arrival rate is manageable. As utilization approaches saturation, requests spend more time waiting; latency can rise sharply rather than proportionally with load. At sustained overload, backlog accumulates over the finite observation window.

An earlier tail-latency crossing does not by itself prove that the underlying service rate changed from 9,000 to 8,800 requests/s. Burstiness, scheduling, generator behavior, and load imbalance can affect the observed boundary. Little's Law, `N = X × R`, concerns mean quantities in a stable system; p99 latency should not be substituted for mean response time, and an unstable overload run should not be treated as a steady-state measurement.

## Experiment 2 Bottleneck analysis

The team compared end-to-end latency from `wrk2` with RPC elapsed times logged by the frontend's gRPC client interceptor. Runs at a reported load of 12,800 requests/s lasted one, two, and five minutes.

The report shows backend RPC latencies remaining comparatively stable while end-to-end tail latency rises with duration. This supports the team's conclusion that the frontend path, rather than a continuously growing detail-service queue, was the likely bottleneck under the tested workload.

The interceptor records elapsed time around the RPC invocation. It is a client-observed RPC duration, not a direct measurement of backend CPU time or queue length. It can include transport and client-side waiting. The scatter plots use request index on the horizontal axis, so they should not be read as uniformly spaced time samples.

The report hypothesizes overhead from RPC routing and JSON serialization. Those explanations remain hypotheses: the supplied artifacts contain no CPU profile, connection-count trace, or direct queue measurements proving the mechanism. Full-payload RPC logging also adds serialization and I/O work in the frontend; logging configuration must be held constant when comparing variants.

## Experiment 3 Frontend replication

The team added frontend replicas and repeated the arrival-rate experiments. With two frontend instances, the report describes latency remaining below 500 ms up to approximately 16,000 requests/s for constant arrivals and approximately 15,600 requests/s for exponential arrivals.

For the diminishing-returns study, the report describes exponential arrivals, two-minute runs, and one through four frontend replicas. The plotted capacity increases through three replicas and changes little at four. Increasing detail replicas did not show an improvement in the reported investigation.

The one-replica point in the capacity-versus-replicas figure appears near 1,000 requests/s, inconsistent with the roughly 9,000 requests/s baseline elsewhere. The original PDF is preserved; that point is not used here to compute a speedup. Likewise, the report's “over 90%” completion criterion does not establish a 99% success rate or fully characterize overload losses.

Diminishing returns can arise when a different component becomes limiting, replicas compete for the VM's finite CPU resources, connections distribute unevenly, or the load generator cannot deliver the requested rate. These are candidate explanations. Establishing the cause would require resource telemetry, per-pod request counts, and verification of actual sent rate.

Scaling the frontend leaves the single detail map shared by all frontend replicas. Scaling the detail service is a different correctness question: independent detail replicas have independent in-memory maps, so reads and writes need a data-consistency strategy before their capacity can be compared meaningfully.

## Optimization investigation

Page 4 discusses a `sync.Map` variant, a connection-related variant, a JSON-library variant, and an Istio proxy proposal or trial. The report describes these observations:

- The map variant produced negligible improvement, consistent with the detail service not being the primary bottleneck in this workload.
- The connection-related variant improved average latency near the tested knee region; the report says tail improvements were less decisive relative to variability.
- The JSON-library variant worsened tail latency in the plotted experiment.
- Proxy overhead outweighed benefits in the reported setup with three frontend instances.

The baseline source already creates and reuses gRPC clients. Without the original variant patch, “connection reuse” cannot identify exactly what changed. Reusing a channel, sending keepalive pings, pooling channels, and streaming RPCs are different techniques. The report's optimization labels are preserved as historical descriptions, not assigned to newly invented implementations.

`sync.Map` is a specialized concurrent map; describing it as universally lock-free or assuming it outperforms a mutex-protected map would require evidence for the tested Go version and access pattern. The original optimization source and proxy configuration are absent from this checkout.

## Scope of the findings

This experiment illustrates earlier tail-latency degradation under bursty load, bottleneck investigation using measurements at different points in a request path, and diminishing returns from replication. The numerical results describe the original team report and its environment; they are not portable throughput guarantees.

The [methodology](experiment-methodology.md) documents the workload and collection process. The [source notes](source-notes.md) identify the retained baseline and small adaptations used to package the frontend/detail path as a standalone showcase.

## Technical references

- [Course queueing-theory discussion](reference/lab2-assignment.md#queueing-theory)
- [gRPC performance guidance](https://grpc.io/docs/guides/performance/), including channel reuse, keepalive, and streams
- [Go concurrent map documentation](https://pkg.go.dev/sync#Map)
