# GCP Experiment Setup and Data Collection

## Historical setup and scope

The Lab 2 experiments ran on GCP. The course instructions use **Kubernetes installed with kubeadm on a Compute Engine VM**, rather than specifying a managed GKE cluster. The recommended VM is `e2-standard-8` with 8 vCPUs and 32 GB RAM, Ubuntu 24.04 LTS on x86-64, and a 20 GB boot disk in `us-west1`. The report does not independently record the actual VM specification or every installed package version.

The original course setup uses a single schedulable control-plane node, a pod network, and container images from a registry. The course deployment template assigns one CPU to an application pod, and the Go entry point sets `GOMAXPROCS(1)`. The load generator runs on the same VM, with logical CPUs 0–2 reserved for it. The showcase manifests explicitly assign one CPU to both application deployments.

This repository preserves the workload and documents that process. The commands below show a reconstructed workflow for an already provisioned Linux VM. The new helper scripts and deployment manifests are showcase additions; they are not recovered historical scripts or exact copies of the deployment that produced the PDF. No cloud resources are created by building or checking this repository.

## Prepare the VM

Use an existing VM with Go, Docker, and a working Kubernetes cluster. Record the actual environment before collecting data:

```bash
uname -a
lscpu
free -h
go version
docker version
kubectl version
kubectl get nodes -o wide
cat /proc/cmdline
```

The course isolated logical CPUs 0–2 by adding `isolcpus=0-2` to the VM's GRUB kernel command line, updating GRUB, and rebooting. `taskset -c 0-2` then placed the generator on those CPUs. CPU affinity for the generator alone does not prove that Kubernetes workloads or interrupts cannot use them; inspect the VM's actual configuration. The old course cgroup settings are historical setup details, not prerequisites imposed by this showcase on current clusters.

Install the load-generator build dependencies on the VM, then build the **bundled course fork**:

```bash
sudo apt-get install build-essential libssl-dev zlib1g-dev luarocks
sudo luarocks install luasocket
make -C wrk2
./wrk2/wrk --help
```

This fork implements `-D const` and `-D exp` and prints separate sent/completed rates. An unmodified upstream `wrk2` is not a drop-in replacement for the Lab 2 commands. The Lua script needs `socket`; check that the installed LuaSocket module is visible to the bundled LuaJIT runtime if module loading fails.

## Deploy the frontend and detail service

Build a registry image and use it for both service roles. Replace the example with a registry path you own and can pull from the VM:

```bash
export LAB2_IMAGE=YOUR_REGISTRY/welp-lab2:showcase
docker build -t "$LAB2_IMAGE" .
docker push "$LAB2_IMAGE"
sed "s|welp-lab2:showcase|${LAB2_IMAGE}|g" manifests/lab2.yaml | kubectl apply -f -
kubectl -n lab2 rollout status deployment/detail
kubectl -n lab2 rollout status deployment/frontend
kubectl -n lab2 get pods -o wide
kubectl -n lab2 get services
```

The manifests use namespace `lab2`, one frontend replica, and one detail replica. Their CPU requests/limits are one CPU per pod. Private images require the cluster's registry access configuration. The frontend Service retains the course endpoint `10.96.88.88:8080`; change that address if the cluster's Service CIDR or existing allocations differ. It is a cluster-internal endpoint, not a public GCP IP.

The source retains the original detail handlers: `GET /post-detail?...` updates a record, and `GET /get-detail?...` reads it. The endpoint named `post-detail` still uses HTTP GET because that is how the course workload is defined.

## Initialize the workload data

Run commands from the repository root because the Lua workload opens `./samples/detail_samples.csv` relative to the current working directory.

```bash
export LAB2_URL=http://10.96.88.88:8080
python3 scripts/seed_details.py --url "$LAB2_URL"
curl --fail "$LAB2_URL/get-detail?restaurant_name=Chick-fil-A"
```

Seeding ensures that the randomized reads can find their records. Record the initial-state procedure when comparing runs. The original report does not specify its exact warm-up or reset protocol, so the explicit seed step here is a reconstruction aid. The Lua workload selects a random record for each operation and issues approximately 80% reads and 20% writes. Its random seed is based on the current time, rather than a stored reproducible seed.

If resetting between experiment conditions, restart the detail deployment, wait for it to become ready, and reseed. Its data is in memory and is lost on restart. Keep this procedure consistent across conditions. The trial helper does not reset the application or silently change replica counts.

## Experiment 1 Arrival pattern and load sweep

A representative one-minute invocation is:

```bash
taskset -c 0-2 ./wrk2/wrk \
  -D const -t 3 -c 90 -d1m \
  -s ./workloads/lab2/simple-detail.lua \
  "$LAB2_URL" -R 9400 -L
```

| Flag | Meaning |
| --- | --- |
| `-D const` / `-D exp` | Constant / exponential inter-arrival distribution |
| `-R 9400` | Configured request arrival rate in requests/s |
| `-t 3` | Three generator threads |
| `-c 90` | Ninety HTTP connections |
| `-d1m` | One-minute observation window |
| `-s ...` | Mixed restaurant-detail workload |
| `-L` | Print the latency percentile distribution |
| `taskset -c 0-2` | Run the generator on selected logical CPUs |

Start at low rates and increase them until latency rises sharply or completed throughput falls behind sent rate. The course recommends doubling initially, then bisecting around the transition. Repeat with exponential arrivals. For each distribution/rate/replica condition, collect at least five trials and keep threads, connections, duration, application state, and logging configuration consistent.

The new collection helper saves the full generator output, experiment metadata, deployment snapshots, and separate logs from every frontend pod:

```bash
# Arguments: distribution, rate, trial, duration, ready frontend replicas.
bash scripts/run_trial.sh const 9400 1 1m 1

# Example repeated condition; this is not the historical full rate sweep.
for trial in 1 2 3 4 5; do
  bash scripts/run_trial.sh const 9400 "$trial" 1m 1
  bash scripts/run_trial.sh exp 9400 "$trial" 1m 1
done
```

Set `LAB2_NAMESPACE`, `LAB2_URL`, or `LAB2_LOAD_CORES` if needed. The helper checks the number of ready frontend replicas; it does not deploy, scale, install software, or provision GCP resources. Inspect logger stderr files for collection failures and confirm every generator thread completes calibration.

## Experiment 2 RPC timing and bottleneck investigation

The original report compares one-, two-, and five-minute runs at a reported load of 12,800 requests/s. The frontend interceptor logs client-observed RPC elapsed time in microseconds. For a single pod, a manual stream is:

```bash
kubectl -n lab2 get pods -l app=frontend
# Replace POD_NAME with a returned frontend pod name.
kubectl -n lab2 logs POD_NAME --tail=0 -f > frontend-rpc.log
```

Start the stream before the workload in another terminal and stop it after the workload. Streaming avoids losing early records to Kubernetes log rotation. Capture all frontend pods when there are multiple replicas. The trial helper manages one stream per frontend pod automatically.

An interceptor record has this structure:

```text
<log date/time> grpc;<RPC method>;<request JSON>;<response JSON>;<error>;<RPC start>;<duration in microseconds>
```

Convert a raw stream to structured CSV or reproduce a request-index latency scatter:

```bash
python3 scripts/parse_logs.py frontend-rpc.csv < frontend-rpc.log
python3 scripts/plot_latency.py frontend-rpc.png < frontend-rpc.log
```

The CSV parser preserves the RPC method, payloads, start time, and duration. Divide `duration_us` by 1,000 for milliseconds. Separate `GetDetail` and `PostDetail` if comparing their behavior. The retained scatter script uses request index, not elapsed time. Analyze whether RPC latency grows throughout the run and compare that trend with the end-to-end p99 measured by `wrk2`.

RPC duration is a proxy for delay along the backend call path; it is not a direct queue-length counter. Account for failed calls, timeouts, logging overhead, and flow control when interpreting stability.

## Experiment 3 Frontend replica scaling

Increase frontend replicas, wait for readiness, and repeat the rate sweep. Keep the detail service at one replica for the main scaling comparison:

```bash
kubectl -n lab2 scale deployment/frontend --replicas=2
kubectl -n lab2 rollout status deployment/frontend
bash scripts/run_trial.sh const 15600 1 1m 2
bash scripts/run_trial.sh exp 15600 1 1m 2
```

The report also describes two-minute exponential-arrival runs while increasing frontend replicas through four. Repeat enough rates to locate the 500 ms boundary for each replica count, rather than measuring only one example rate.

Define a capacity point using the highest measured completed throughput that satisfies the latency target and a separately stated error/completion criterion. Do not call an already overloaded run the maximum acceptable capacity. Verify that the sent rate matches the requested rate and check generator CPU usage before attributing a plateau to the services.

## Aggregate and plot collected trials

The new scripts can process newly collected run artifacts:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/summarize_wrk.py results/runs --output results/trials.csv
python3 scripts/plot_results.py results/trials.csv --output results/p99-vs-load.png
python3 scripts/plot_results.py results/trials.csv \
  --x completed_rps --output results/p99-vs-throughput.png
```

The summary includes sent/completed rates, mean/p99 latency, completed responses, HTTP status errors, socket errors, timeouts, and process exit status. The plot groups by distribution, frontend replicas, duration, and configured rate. It averages trial p99 values and uses population standard deviation, matching the original course plotting helper's `numpy.std` convention. Error bars describe between-trial spread, not confidence intervals.

The plot rejects nonzero process exits, but HTTP errors and incomplete responses still require review. A successful exit alone does not make a capacity point acceptable. When plotting against measured throughput, the horizontal position is the average completed rate across the repeated condition.

The supplied report-summary CSV is a different artifact: it is a transcription of historical aggregate values and is not accepted as a run-summary substitute. The original figures remain available in the PDF without requiring GCP access or reconstructing missing raw trials.

## References

- [Original Lab 2 tutorial and requirements](reference/lab2-assignment.md)
- [Course GCP setup](https://github.com/ucsd-cse190-wi25/cse190-labs/blob/main/docs/lab0.md)
- [Course application setup](https://github.com/ucsd-cse190-wi25/cse190-labs/blob/main/docs/lab1.md)
- [Original report](../reports/lab2-analysis.pdf)
- [Data artifact descriptions](../results/README.md)
