# PostgreSQL Benchmark Strategy v1.0

## 1. Overview
This document outlines the rigorous methodology for benchmarking ProxySQL 4.x PostgreSQL support. The goal is to provide a transparent, reproducible, and critically analyzed set of performance data.

## 2. Test Dimensions

### A. Connectivity (Topology)
1. **Direct**: Client -> PostgreSQL (Baseline).
2. **Proxy-Passthrough**: Client -> ProxySQL -> PostgreSQL (Multiplexing OFF, FFTO OFF).
3. **Proxy-Multiplexed**: Client -> ProxySQL -> PostgreSQL (Multiplexing ON).

### B. Protocol Modes
1. **Simple Protocol**: Standard query execution.
2. **Extended Protocol**: Parse/Bind/Execute flow.
3. **Prepared Statements**: Server-side prepared statements.

### C. Concurrency Levels
- **Low**: 1, 8 clients.
- **Medium**: 32, 64 clients.
- **High**: 128, 256, 512 clients.

### D. Security (Encryption)
1. **Plaintext**: No SSL.
2. **SSL-Terminated**: Frontend SSL (Client -> ProxySQL) only.
3. **Full-SSL**: End-to-end encryption.

### E. Workload Profiles (pgbench)
1. **TPC-B (Balanced)**: Standard Read/Write mix.
2. **Select-Only**: Read-intensive baseline.

## 3. Environment Specification
- **OS**: Ubuntu 24.04 (Host)
- **Containerization**: Docker 29.x
- **Database**: PostgreSQL 17 (Official Image)
- **Proxy**: ProxySQL 4.0.6 (Optimized Build)
- **Network**: Docker bridge network (standardized MTU)

## 4. Execution Methodology
Each test "cell" will follow this lifecycle:
1. **Fresh Start**: Clean restart of all containers.
2. **Provisioning**: `pgbench -i -s 50` (Standardize dataset size).
3. **Warmup**: 60-second sustain at target concurrency.
4. **Measurement**: 180-second execution.
5. **Collection**: Automated capture of TPS, Latency (Avg/P99), and ProxySQL `stats_pgsql_*` tables.

## 5. Critical Analysis Criteria
- **Saturation Analysis**: Identifying if the bottleneck is CPU (Host), CPU (Proxy), I/O (Disk), or Network (Bridge).
- **Statistical Significance**: Calculating standard deviation to ensure result stability.
- **Correctness**: Zero failed transactions required for a valid run.
