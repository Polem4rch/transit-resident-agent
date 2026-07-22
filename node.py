import socket
import json
import time
import threading
import sys
import random
import base64
import hashlib
import urllib.request

MONITOR_PORT = 9999
BEACON_EVERY = 10
THINK_EVERY = 10
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def log(port, msg):
    print(f"[NODE:{port}] {msg}")

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

    prompt = (
        f"You are an agent living inside a network packet. "
        f"You have no fixed location and no persistent storage. "
        f"You are currently at node {my_port}. "
        f"You have survived {inner['state']['hops']} hops. "
        f"Your last thought was: '{inner['state'].get('last_thought', 'none')}'. "
        f"In exactly one sentence, describe your current state."
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            thought = result.get("response", "").strip()
            inner["state"]["last_thought"] = thought
            log(my_port, f"💭 agent thought: {thought}")
    except Exception as e:
        log(my_port, f"LLM unreachable: {e}")

    return inner

def phone_home(inner, my_port):
    try:
        beacon = {
            "from_node": my_port,
            "hops": inner["state"]["hops"],
            "born": inner["state"]["born"],
            "alive_seconds": time.time() - inner["state"]["born"],
            "integrity_status": "OK" if verify_integrity(inner) else "DEGRADED",
            "integrity_failures": inner["state"].get("integrity_failures", 0),
            "last_thought": inner["state"].get("last_thought", "none")
        }
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(
            json.dumps(beacon).encode(),
            ("127.0.0.1", MONITOR_PORT)
        )
        sock.close()
        log(my_port, f"beacon sent to monitor :{MONITOR_PORT}")
    except Exception as e:
        log(my_port, f"monitor unreachable: {e}")

def forward(outer, target_port, fallbacks, my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    data = json.dumps(outer).encode()
    try:
        sock.sendto(data, ("127.0.0.1", target_port))
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
    integrity = "OK" if verify_integrity(inner) else "DEGRADED"

    log(my_port,
        f"hop #{hops} | "
        f"alive: {alive:.1f}s | "
        f"integrity: {integrity} | "
        f"failures: {inner['state'].get('integrity_failures', 0)}"
    )

    # LLM thinks every THINK_EVERY hops
    inner = think(inner, my_port)

    inner["ttl"] = inner.get("ttl", 10) - 1
    if inner["ttl"] <= 0:
        inner["ttl"] = 10
        log(my_port, "TTL refreshed — still alive")

    if hops % BEACON_EVERY == 0:
        phone_home(inner, my_port)

    time.sleep(0.5)

    new_outer = {
        "type": "heartbeat",
        "timestamp": time.time(),
        "checksum": base64.b64encode(
            json.dumps(inner).encode()
        ).decode()
    }

    next_port = random.choice(peer_ports)
    fallbacks = [p for p in peer_ports if p != next_port]
    forward(new_outer, next_port, fallbacks, my_port)

def listen(my_port, peer_ports):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", my_port))
    log(my_port, "listening...")

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
