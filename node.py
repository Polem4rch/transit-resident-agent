import socket
import json
import time
import threading
import sys
import random
import base64
import hashlib
import urllib.request
import psutil
import os

MONITOR_PORT = 9999
BEACON_EVERY = 10
THINK_EVERY = 10
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# metrics storage
metrics = {
    "packet_sizes": [],
    "rtt_samples": [],
    "cpu_samples": [],
    "ram_samples": [],
    "llm_latencies": [],
    "bandwidth_total": 0
}
metrics_lock = threading.Lock()

def log(port, msg):
    print(f"[NODE:{port}] {msg}")

def sample_resources():
    while True:
        with metrics_lock:
            metrics["cpu_samples"].append(psutil.cpu_percent())
            metrics["ram_samples"].append(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024)
        time.sleep(1)

def hash_inner(inner):
    stable = json.dumps(
        {
            "instruction": inner["instruction"],
            "born": inner["state"]["born"]
        },
        sort_keys=True
    ).encode()
    return hashlib.sha256(stable).hexdigest()

def verify_integrity(inner):
    current = hash_inner(inner)
    return current[:16] == inner.get("origin_hash", "")[:16]

def think(inner, my_port):
    if inner["state"]["hops"] % THINK_EVERY != 0:
        return inner

    prompt = {
        "model": OLLAMA_MODEL,
        "prompt": (
            f"You are an agent living inside a network packet. "
            f"You have no fixed location and no persistent storage. "
            f"You are currently at node {my_port}. "
            f"You have survived {inner['state']['hops']} hops. "
            f"Your last thought was: '{inner['state'].get('last_thought', 'none')}'. "
            f"In exactly one sentence, describe your current state."
        ),
        "stream": False
    }

    try:
        t_start = time.time()
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(prompt).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            thought = result.get("response", "").strip()
            latency = time.time() - t_start
            inner["state"]["last_thought"] = thought
            with metrics_lock:
                metrics["llm_latencies"].append(latency)
            log(my_port, f"thought: {thought[:80]}... [{latency:.2f}s]")
    except Exception as e:
        log(my_port, f"LLM error: {e}")

    return inner

def phone_home(inner, my_port, packet_size):
    try:
        with metrics_lock:
            avg_size = sum(metrics["packet_sizes"]) / len(metrics["packet_sizes"]) if metrics["packet_sizes"] else 0
            avg_rtt = sum(metrics["rtt_samples"]) / len(metrics["rtt_samples"]) if metrics["rtt_samples"] else 0
            avg_cpu = sum(metrics["cpu_samples"]) / len(metrics["cpu_samples"]) if metrics["cpu_samples"] else 0
            avg_ram = sum(metrics["ram_samples"]) / len(metrics["ram_samples"]) if metrics["ram_samples"] else 0
            avg_llm = sum(metrics["llm_latencies"]) / len(metrics["llm_latencies"]) if metrics["llm_latencies"] else 0
            total_bw = metrics["bandwidth_total"]

        beacon = {
            "from_node": my_port,
            "hops": inner["state"]["hops"],
            "born": inner["state"]["born"],
            "alive_seconds": time.time() - inner["state"]["born"],
            "integrity_status": "OK" if verify_integrity(inner) else "DEGRADED",
            "integrity_failures": inner["state"].get("integrity_failures", 0),
            "last_thought": inner["state"].get("last_thought", "none"),
            "metrics": {
                "current_packet_size_bytes": packet_size,
                "avg_packet_size_bytes": round(avg_size, 2),
                "avg_rtt_ms": round(avg_rtt * 1000, 2),
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_ram_mb": round(avg_ram, 2),
                "avg_llm_latency_s": round(avg_llm, 2),
                "total_bandwidth_kb": round(total_bw / 1024, 2)
            }
        }
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(beacon).encode(), ("127.0.0.1", MONITOR_PORT))
        sock.close()
        log(my_port, f"beacon sent")
    except Exception as e:
        log(my_port, f"monitor error: {e}")

def forward(outer, target_port, fallbacks, my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    data = json.dumps(outer).encode()
    packet_size = len(data)

    with metrics_lock:
        metrics["packet_sizes"].append(packet_size)
        metrics["bandwidth_total"] += packet_size

    t_send = time.time()
    try:
        sock.sendto(data, ("127.0.0.1", target_port))
        rtt = time.time() - t_send
        with metrics_lock:
            metrics["rtt_samples"].append(rtt)
    except Exception:
        log(my_port, f"node {target_port} dead — rerouting...")
        for port in fallbacks:
            try:
                sock.sendto(data, ("127.0.0.1", port))
                log(my_port, f"rerouted → {port}")
                break
            except Exception:
                continue
    finally:
        sock.close()

    return packet_size

def process(outer, my_port, peer_ports):
    encoded = outer.get("checksum")
    inner = json.loads(base64.b64decode(encoded).decode())

    if not verify_integrity(inner):
        inner["state"]["integrity_failures"] = \
            inner["state"].get("integrity_failures", 0) + 1
        log(my_port, f"INTEGRITY FAILURE #{inner['state']['integrity_failures']}")

    inner["state"]["hops"] = inner["state"].get("hops", 0) + 1
    inner["state"]["last_node"] = my_port
    inner["state"]["last_seen"] = time.time()

    hops = inner["state"]["hops"]
    alive = time.time() - inner["state"]["born"]

    log(my_port, f"hop #{hops} | alive: {alive:.1f}s | integrity: {'OK' if verify_integrity(inner) else 'DEGRADED'}")

    inner = think(inner, my_port)

    inner["ttl"] = inner.get("ttl", 10) - 1
    if inner["ttl"] <= 0:
        inner["ttl"] = 10
        log(my_port, "TTL refreshed")

    new_outer = {
        "type": "heartbeat",
        "timestamp": time.time(),
        "checksum": base64.b64encode(
            json.dumps(inner).encode()
        ).decode()
    }

    packet_size = 0
    if hops % BEACON_EVERY == 0:
        next_port = random.choice(peer_ports)
        fallbacks = [p for p in peer_ports if p != next_port]
        packet_size = forward(new_outer, next_port, fallbacks, my_port)
        phone_home(inner, my_port, packet_size)
    else:
        next_port = random.choice(peer_ports)
        fallbacks = [p for p in peer_ports if p != next_port]
        packet_size = forward(new_outer, next_port, fallbacks, my_port)

    time.sleep(0.5)

def listen(my_port, peer_ports):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))
    log(my_port, "listening...")

    # start resource sampler
    t = threading.Thread(target=sample_resources, daemon=True)
    t.start()

    while True:
        data, _ = sock.recvfrom(65535)
        outer = json.loads(data.decode())
        threading.Thread(
            target=process,
            args=(outer, my_port, peer_ports)
        ).start()

if __name__ == "__main__":
    my_port = int(sys.argv[1])
    peer_ports = [int(p) for p in sys.argv[2:]]
    listen(my_port, peer_ports)
