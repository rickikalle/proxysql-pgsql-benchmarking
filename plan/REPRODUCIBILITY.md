# PostgreSQL Benchmark Reproducibility Guide

## 1. Prerequisites
- **Docker & Docker Compose**: For environment isolation.
- **Python 3.x**: For the execution harness.
- **ProxySQL 4.0.6 Binary**: Must be present at `./src/proxysql`.

## 2. Automated Harness (`harness.py`)
The benchmark is controlled by a Python script that ensures consistency across runs. It performs:
1. **Network Reset**: Recreates the `pgsql_bench_net` bridge.
2. **Container Lifecycle**: Stops and starts Postgres/ProxySQL containers from clean images.
3. **Configuration Injection**: Applies specific ProxySQL variables (Multiplexing, SSL, etc.) via the Admin interface.
4. **Data Population**: Runs `pgbench -i -s 50` to ensure a consistent dataset.
5. **Phase Execution**: Loops through the Concurrency Matrix (1, 16, 64, 128, 256).
6. **Data Capture**: Redirects `pgbench` results to `results/raw_<test_id>.txt` and snapshots ProxySQL stats.

## 3. Environment Variables
```bash
export PG_IMAGE="postgres:17"
export PROXYSQL_BIN="./src/proxysql"
export SCALE_FACTOR=50
export DURATION=180
```

## 4. Manual Verification
To manually verify a specific scenario (e.g., Extended Protocol, 64 clients):
```bash
docker run --rm --network pgsql_bench_net postgres:17 \
    pgbench -M extended -c 64 -j 4 -T 60 -h proxysql -p 6133 -U postgres postgres
```

## 5. Result Validation
A result is considered valid only if:
- Transaction failure rate is 0.00%.
- Latency standard deviation is < 15% of the mean.
- ProxySQL log shows no "Critical" or "Error" events during the measurement window.
