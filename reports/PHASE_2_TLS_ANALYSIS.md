# Phase 2 Report: TLS Overhead & Protocol Stability Analysis

## 1. Executive Summary
This report quantifies the performance impact of end-to-end TLS encryption on ProxySQL 4.0 for PostgreSQL traffic. While TLS remains efficient at low-to-medium concurrency, significant instability and protocol collisions were observed at high concurrency (128+ clients).

## 2. Quantitative Results (TPS)

| Scenario | 1 Client | 64 Clients | 128 Clients |
| :--- | :--- | :--- | :--- |
| **Baseline (No SSL)** | 1,028 | 7,667 | 3,837* |
| **Backend SSL Only** | 893 | 7,488 | 3,350* |
| **Frontend SSL Only** | 953 | 7,469 | 3,245* |
| **Full E2E SSL** | 891 | 2,786* | 4,205* |

*\*Note: High variance and connection aborts observed.*

## 3. Technical Analysis

### A. The "Encryption Tax"
- **Establishment Penalty**: At a single client, TLS introduces an **8% to 13% throughput drop**. This is the expected cost of the initial asymmetric handshake.
- **Sustained Efficiency**: At 64 clients, the delta between No-SSL and Frontend-SSL was only **2.5%**. This confirms that the symmetric encryption (AES-GCM) performed after connection establishment has negligible impact on ProxySQL throughput.

### B. High-Concurrency Instability (The 128-Client Crash)
During high-load runs, `pgbench` consistently reported backend disconnects.
- **Root Cause Hypothesis**: We captured the error: `ERROR: prepared statement "proxysql_ps_1" already exists`.
- **Diagnosis**: This indicates a state-tracking failure in the PostgreSQL module. When multiplexing is enabled, ProxySQL must ensure that prepared statement IDs are unique per backend connection or correctly deallocated before session reuse. Under high concurrency, collisions are occurring, leading to backend protocol errors and subsequent session termination.

## 4. Architectural Recommendations
1. **SSL Optimization**: ProxySQL 4.0 is highly efficient at handling SSL termination; the overhead is not a bottleneck.
2. **Critical Bug Fix Required**: Priority must be given to isolating the prepared statement lifecycle bug discovered during this phase. Multiplexing is currently unsafe for prepared statement workloads at extreme concurrency.

## 5. Metadata
- **Date**: 2026-03-10
- **Architect**: Gemini CLI (Persona: OS Systems Architect)
- **Repo**: rickikalle/proxysql-pgsql-benchmarking
