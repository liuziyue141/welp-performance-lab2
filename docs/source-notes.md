# Source Provenance and Showcase Adaptations

## Available source

The source was extracted from the supplied `cse190-labs` checkout at commit `8ede45dc5f8d5b6934c44d6b14575a40a2fd7f70`, whose origin is [ucsd-cse190-wi25/cse190-labs](https://github.com/ucsd-cse190-wi25/cse190-labs). That checkout contains the course baseline and multiple lab scaffolds, rather than the team's final optimization patches.

The detail service, detail Protobuf files, sample dataset, Lua workloads, customized `wrk2` source, and request-index RPC plotting script are retained from that checkout. `wrk2` keeps its upstream README, license, notices, and LuaJIT sources; its course-specific `-D` behavior is documented in the experiment workflow.

## Changes for this repository

- `services/frontend.go` keeps the original detail HTTP handlers and client creation, removes unused review/reservation/static routes, and uses a dedicated HTTP mux.
- `services/utils.go` retains the RPC interceptor and gRPC dial helper, removing the UUID utility used outside the Lab 2 path.
- `cmd/main.go` exposes only frontend and detail roles, preserves `GOMAXPROCS(1)`, and parses flags after the service role explicitly.
- The Dockerfile and complete frontend/detail manifests package that subset. The manifests reconstruct the documented topology; they are not recovered historical deployment files.
- The seeding, trial-collection, summary, and aggregate-plot scripts are new helpers explaining the collection workflow. The RPC CSV parser is corrected to retain the method name and handle semicolons inside JSON payloads.
- Review/reservation services, cache/storage labs, their tests, and unrelated course setup scripts are omitted.
- The original PDF is copied byte-for-byte. `results/report-summary.csv` contains explicitly transcribed aggregate values, not generated measurements.
- The Go module retains the original gRPC/Protobuf versions and removes dependencies needed only by omitted labs. Assignment illustration links are adjusted to the new directory layout.

Removing unrelated routes, changing the HTTP mux, rebuilding with a different toolchain, or using the reconstructed manifests can affect performance. This package is not claimed to be a bit-for-bit copy of the GCP deployment behind the report.

## Historical material

The original report credits Chris Kim, Jared Jose, and Ziyue Liu. It is preserved as the main historical artifact. The accompanying write-up explains inconsistencies rather than silently editing the original figures or conclusions. The supplied materials do not establish which implementation tasks each teammate performed.

The original raw trials, installed environment inventory, optimization patches, and Istio deployment configuration were not supplied. Their absence is recorded here so the available source is not mistaken for a complete archive of every experiment variant.
