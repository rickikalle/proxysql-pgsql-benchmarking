# PostgreSQL Benchmarking Results

## Environment
- **ProxySQL**: 4.0.6-900-g9d921bd (Non-debug)
- **PostgreSQL**: 17 (Docker)
- **Workload**: TPC-B (pgbench)
- **Scale**: 10

## Results Matrix

| Configuration | Protocol | Clients | TPS | Avg Latency | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Direct (Metal) | Simple | 16 | 8725 | 1.83 ms | Baseline |
| ProxySQL | Simple | 16 | 6108 | 2.62 ms | ~30% Protocol Overhead |
| ProxySQL | Extended | 16 | 7000 | 2.28 ms | ~20% Protocol Overhead |
| ProxySQL | Extended | 128 | 6214 | 20.58 ms | Backend connection pressure |
| ProxySQL + Mux | Extended | 128 | 7029 | 18.20 ms | **13% Improvement** via Multiplexing |
| ProxySQL + Mux + FFTO | Extended | 128 | 6424 | 19.91 ms | FFTO overhead observed |

## Observations
1. **Extended Protocol Efficiency**: The Extended Query Protocol performs significantly better than the Simple protocol (~15% higher TPS), likely due to reduced parsing overhead on the backend and more efficient message handling in ProxySQL.
2. **Multiplexing Impact**: At high concurrency (128 clients), enabling `pgsql-multiplex_enabled` provided a clear performance boost, bringing TPS back up to 7000+ by reducing backend connection churn.
3. **FFTO Overhead**: In this specific TPC-B workload (which involves multiple small statements per transaction), FFTO introduced a slight latency overhead. FFTO is likely more beneficial for specific high-volume, single-query streaming patterns.
4. **Stability**: Once the initial configuration sequence was stabilized (avoiding rapid LOAD commands during background startup), the PostgreSQL module handled 128 concurrent clients with zero failed transactions.
