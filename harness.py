import subprocess
import time
import json
import os
import sys
import re

# Absolute paths for stability
BASE_DIR = "/home/ricki/pgsql_benchmarking"
PROXYSQL_BIN = "/home/ricki/proxysql/src/proxysql"
PROXYSQL_CONFIG = "/home/ricki/proxysql/test/infra/control/proxysql-ci.cnf"
DATA_DIR = f"{BASE_DIR}/proxysql_data"
RESULTS_DIR = f"{BASE_DIR}/results"
COMPOSE_FILE = f"{BASE_DIR}/docker-compose.yml"

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def run_cmd(cmd, timeout=300):
    log(f"Executing: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            log(f"Command failed with code {result.returncode}")
            log(f"Stderr: {result.stderr}")
        return result
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout}s")
        return None

def setup_env():
    log("Cleaning up environment...")
    run_cmd("docker rm -f benchmark_pg_master || true", timeout=30)
    log("Starting containers...")
    run_cmd(f"docker compose -f {COMPOSE_FILE} up -d", timeout=60)
    log("Waiting for Postgres to initialize...")
    time.sleep(15)

def get_gateway_ip():
    res = run_cmd("docker network inspect pgsql_benchmarking_benchmark_net -f '{{range .IPAM.Config}}{{.Gateway}}{{end}}'")
    if res and res.returncode == 0:
        return res.stdout.strip()
    return "172.25.0.1"

def configure_proxysql(multiplex=False):
    log(f"Configuring ProxySQL (Multiplexing: {multiplex})...")
    run_cmd("pkill -9 proxysql", timeout=10)
    run_cmd(f"rm -rf {DATA_DIR} && mkdir -p {DATA_DIR}", timeout=10)
    
    # Start ProxySQL
    cmd = f"{PROXYSQL_BIN} -f -c {PROXYSQL_CONFIG} -D {DATA_DIR} > {DATA_DIR}/proxysql.log 2>&1 &"
    subprocess.Popen(cmd, shell=True)
    time.sleep(5)
    
    admin_cmd = "mysql -uadmin -padmin -h127.0.0.1 -P6032 -e"
    pwd = "benchmark_pass"
    
    # Basic Config
    run_cmd(f"{admin_cmd} \"INSERT INTO pgsql_servers (hostname, port) VALUES ('172.25.0.2', 5432); LOAD PGSQL SERVERS TO RUNTIME;\"")
    run_cmd(f"{admin_cmd} \"INSERT INTO pgsql_users (username, password) VALUES ('postgres', '{pwd}'); LOAD PGSQL USERS TO RUNTIME;\"")
    run_cmd(f"{admin_cmd} \"INSERT INTO pgsql_query_rules (rule_id, destination_hostgroup, apply) VALUES (1, 0, 1); LOAD PGSQL QUERY RULES TO RUNTIME;\"")
    
    mux_val = 'true' if multiplex else 'false'
    run_cmd(f"{admin_cmd} \"UPDATE global_variables SET variable_value='{mux_val}' WHERE variable_name='pgsql-multiplex_enabled'; LOAD PGSQL VARIABLES TO RUNTIME;\"")

def run_benchmark(host, port, user, password, clients, threads, duration, mode="simple"):
    query_mode = "simple" if mode == "simple" else "extended"
    log(f"Running Benchmark: {mode}, {clients} clients, {duration}s")
    cmd = f"docker run --rm --network pgsql_benchmarking_benchmark_net -e PGPASSWORD={password} postgres:17 pgbench -c {clients} -j {threads} -T {duration} -P 5 -h {host} -p {port} -U {user} -M {query_mode} postgres"
    
    res = run_cmd(cmd, timeout=duration + 120)
    return res.stdout if res else ""

def parse_tps(output):
    match = re.search(r"tps = ([\d\.]+)", output)
    return float(match.group(1)) if match else 0.0

def main():
    concurrencies = [1, 16, 64, 128]
    duration = 60
    results = []
    
    setup_env()
    gateway = get_gateway_ip()
    log(f"Infrastructure ready. Gateway: {gateway}")
    
    # 1. Direct Baseline
    log("=== Phase 1: Direct Baseline ===")
    run_cmd(f"docker run --rm --network pgsql_benchmarking_benchmark_net -e PGPASSWORD=benchmark_pass postgres:17 pgbench -i -s 10 -h 172.25.0.2 -p 5432 -U postgres postgres")
    for c in concurrencies:
        out = run_benchmark("172.25.0.2", 5432, "postgres", "benchmark_pass", c, min(c, 8), duration)
        results.append({"test": "direct", "clients": c, "tps": parse_tps(out), "mode": "simple"})

    # 2. Proxy Passthrough
    log("=== Phase 2: Proxy Passthrough (Simple & Extended) ===")
    configure_proxysql(multiplex=False)
    for mode in ["simple", "extended"]:
        for c in concurrencies:
            out = run_benchmark(gateway, 6133, "postgres", "benchmark_pass", c, min(c, 8), duration, mode=mode)
            results.append({"test": f"proxy_passthrough", "clients": c, "tps": parse_tps(out), "mode": mode})

    # 3. Proxy Multiplexed
    log("=== Phase 3: Proxy Multiplexed ===")
    configure_proxysql(multiplex=True)
    for c in concurrencies:
        out = run_benchmark(gateway, 6133, "postgres", "benchmark_pass", c, min(c, 8), duration, mode="extended")
        results.append({"test": "proxy_multiplexed", "clients": c, "tps": parse_tps(out), "mode": "extended"})

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(f"{RESULTS_DIR}/summary.json", "w") as f:
        json.dump(results, f, indent=2)
    
    log(f"Benchmark complete. Results in {RESULTS_DIR}/summary.json")

if __name__ == "__main__":
    main()
