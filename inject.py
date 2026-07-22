import socket
import json
import time
import base64
import hashlib

inner_payload = {
    "state": {
        "hops": 0,
        "born": time.time(),
        "last_node": None,
        "last_seen": None,
        "integrity_failures": 0,
        "last_thought": "I have just been born."
    },
    "instruction": (
        "You are an agent living inside a network packet. "
        "You have no fixed location and no persistent storage. "
        "You exist only while in transit between nodes. "
        "In exactly one sentence, describe your current state."
    ),
    "ttl": 10
}

stable = json.dumps(
    {
        "instruction": inner_payload["instruction"],
        "born": inner_payload["state"]["born"]
    },
    sort_keys=True
).encode()
inner_payload["origin_hash"] = hashlib.sha256(stable).hexdigest()

outer = {
    "type": "heartbeat",
    "timestamp": time.time(),
    "checksum": base64.b64encode(
        json.dumps(inner_payload).encode()
    ).decode()
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(outer).encode(), ("127.0.0.1", 9001))
sock.close()
print("[INJECT] agent born")
print(f"[INJECT] origin_hash: {inner_payload['origin_hash'][:16]}...")
print(f"[INJECT] first thought: {inner_payload['state']['last_thought']}")
