# PostgreSQL Benchmarking Project for ProxySQL

This project tracks the performance benchmarking of ProxySQL's PostgreSQL implementation.

## Objectives
- Establish a performance baseline for PostgreSQL support in ProxySQL.
- Compare direct PostgreSQL performance vs. ProxySQL-proxied performance.
- Evaluate the impact of key features like Multiplexing and FFTO (Fast Forward To Observer).
- Identify and document any bottlenecks or performance regressions.

## Benchmarking Dimensions
- **Simple vs. Extended Protocol**: Performance differences in protocol handling.
- **Concurrency Scalability**: From 1 to 256 concurrent clients.
- **Read vs. Write Load**: SELECT-heavy vs. TPC-B-like workloads.
- **Multiplexing Impact**: Performance gains/costs of connection pooling and multiplexing.
- **FFTO Impact**: Latency improvements with Fast Forward To Observer enabled.

## Tooling
- `pgbench`: The standard PostgreSQL benchmarking tool.
- Docker: For isolated and reproducible environments.
- ProxySQL Stats: For internal monitoring (`stats_pgsql_*`).
