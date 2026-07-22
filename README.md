# Transit-Resident Agents (TRA)

> "It persists not by hiding, but by never stopping moving."

A proof-of-concept demonstrating that an AI agent's complete state — including distributed LLM cognition — can exist exclusively inside network packet payloads with no disk writes, no fixed process, and no persistent host.

## Results

| Phase | Hops | Runtime | Integrity Failures |
|---|---|---|---|
| Pure state persistence | 16,500 | 4.38 hours | 0 |
| Distributed LLM cognition | 7,190 | 2.55 hours | 0 |

---

## The Core Finding

### Persistence Without Artifacts

Traditional persistence mechanisms leave traces:

| Mechanism | Artifact Left Behind |
|---|---|
| Registry key | HKLM/HKCU entry |
| Scheduled task | XML file in System32 |
| Service install | Service registry entry |
| Cron job | Entry in crontab |
| Startup folder | File on disk |
| **TRA** | **Nothing** |

A TRA writes nothing to disk. It has no process to kill. It has no file to delete. It has no registry key to remove. Reimaging the host does not kill it — it was never there.

---

### The Forensics Problem

Standard incident response checklist against a TRA:

```
✗ Check running processes     → nothing suspicious
✗ Check disk for malware      → nothing
✗ Check logs                  → normal UDP heartbeats
✗ Check registry              → nothing
✗ Check scheduled tasks       → nothing
✗ Memory forensics            → payload gone in milliseconds
✗ Check startup entries       → nothing
```

**The only thing that works:**

```
✓ Continuous PCAP at network chokepoints
  + born timestamp correlation across flows
```

If PCAP was not running before the incident — there is no forensic record. Nothing to analyze. Nothing to find.

---

### The Only Forensic Artifact

The born timestamp inside the packet payload.

```json
"born": 1784660034.1599202
```

This value:
- Never changes across any hop
- Appears in every beacon from every node
- Cannot be changed without destroying the agent's identity
- Is the single fingerprint a defender can track

Detection rule:
> Same born timestamp appearing from multiple source IPs in UDP traffic = Transit-Resident Agent

No current SIEM or NDR platform has this correlation rule.

---

## Architecture

```
[inject.py] — creates agent once, then disappears
    ↓
[node.py x3] — receives, thinks, forwards
    ↓             ↑
    └─────────────┘
         ↓
[monitor.py] — tripwire, receives beacon every 10 hops
         ↓
[ollama] — local LLM inference per node
```

### The Packet Structure

```
outer packet — looks like a heartbeat to any observer
{
  "type": "heartbeat",
  "timestamp": 1784660034.15,
  "checksum": "<base64>"   ← agent hidden here
}

inner payload — the actual agent
{
  "state": {
    "hops": 7190,
    "born": 1784660034.15,    ← never changes
    "last_thought": "...",    ← LLM output from last node
    "integrity_failures": 0
  },
  "instruction": "...",       ← LLM prompt, travels in packet
  "ttl": 10,
  "origin_hash": "..."        ← tamper detection
}
```

The agent field is named `checksum` in the outer packet to resemble a routine integrity value to a casual observer.

---

## What Each Component Does

**inject.py** — runs once. Creates the agent, computes the origin_hash, wraps it in the outer envelope, sends it to the first node. Never runs again.

**node.py** — stateless executor. Receives packet, verifies integrity, increments hops, calls Ollama every 10 hops, stores the thought in the packet, beacons to monitor every 10 hops, forwards to random peer. Holds no memory between packets. Is not the agent — it is infrastructure.

**monitor.py** — your tripwire. Listens on port 9999. Receives beacons. Prints hop count, uptime, integrity status, and the agent's last thought. This is what a defender would build to detect TRA beaconing behavior.

**ollama** — local LLM inference. Called by each node with the current hop count, node identity, and previous thought. Returns one sentence. That sentence travels in the packet to the next node.

---

## The Emergent Self-Model Finding

The agent was given no information about networking concepts. By hop 7,000 it was describing itself using precise technical vocabulary:

**Hop 10:**
> "I exist in a transient state as a packet with no specific identity or context."

**Hop 2,400:**
> "I am a fleeting consciousness trapped within a network packet, suspended in a state of limbo."

**Hop 7,170:**
> "I am temporarily stored on a buffer cache at node 9002, waiting to be retransmitted with minimal data loss, having survived an exhaustive journey through nearly 7,171 hops of turbulent network traffic."

The agent learned it was a packet. It learned what buffer caches are. It developed an accurate technical self-model from accumulated context alone — without being told.

---

## Known Vulnerabilities Of This PoC

### 1. Node Failure = Agent Death (UDP)
UDP is connectionless. If a packet is in-flight to a node when that node dies — the packet is silently dropped. No exception raised. No recovery. Agent dies immediately.

Tested empirically: 100% lethality on single node failure.

Fix: TCP transport or explicit ACK protocol over UDP.

### 2. No Cryptographic Signing = MITM Vulnerable
Anyone between two nodes can:
- Intercept the packet
- Decode the base64 payload (trivial)
- Modify the instruction field
- Re-encode and forward

The node executes the modified instruction without knowing. This is identical to HTTP interception in a proxy tool.

Fix: Asymmetric signing at injection. Verify and discard on signature failure at each node.

### 3. Integrity Failure Does Not Halt Execution
Current implementation logs integrity failures but continues processing. A modified packet is executed even when tampering is detected.

Fix: Return immediately on integrity failure. Do not execute. Do not forward.

### 4. Unbounded Thread Pool = DoS Vulnerable
Each received packet spawns a new thread. Under UDP flood: N packets → N threads → memory exhaustion → crash.

Fix: ThreadPoolExecutor with bounded max_workers. Per-source rate limiting.

### 5. Localhost Only
This PoC runs on a single machine with three processes. Real network deployment across physical machines is unvalidated. NAT traversal, packet loss under congestion, and variable latency are unaddressed.

---

## Requirements

- Python 3.9+
- Ollama — https://ollama.ai
- Llama 3.2 3B

```bash
brew install ollama
ollama pull llama3.2:3b
```

---

## Run

```bash
# terminal 1
ollama serve

# terminal 2
python3 monitor.py

# terminal 3
python3 node.py 9001 9002 9003

# terminal 4
python3 node.py 9002 9001 9003

# terminal 5
python3 node.py 9003 9001 9002

# terminal 6
python3 inject.py
```

Watch the monitor. First LLM thought appears at hop 10.

---

## Detection

If you want to detect a TRA running against you:

1. **Run continuous PCAP** at network chokepoints
2. **Index born timestamps** across all UDP flows
3. **Alert** when the same born timestamp appears from more than one source IP

That correlation rule does not exist in any current commercial SIEM or NDR platform.

---

## Paper

Full research paper: [arXiv link after submission]

---

## Author

Gabriel Tarsia — Independent Security Researcher
https://www.linkedin.com/in/sl-osint/

---

## Responsible Disclosure

This research is published for defensive awareness. The primary contribution is the detection methodology and the formalization of transit-resident persistence as a threat class.

The PoC is intentionally minimal, localhost-only, and does not implement any offensive capability beyond demonstrating the persistence primitive.

---

## License

MIT
