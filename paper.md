# Transit-Resident Agents: When the Packet IS the Agent

**Gabriel Tarsia**
Independent Security Researcher
https://www.linkedin.com/in/sl-osint/

---

## Abstract

Contemporary threat models for autonomous AI agents assume a fixed infrastructure substrate — a server, container, or persistent process that houses the agent's state and reasoning. This paper challenges that assumption. We propose and demonstrate Transit-Resident Agents (TRAs): a model in which an agent's complete state exists exclusively within encapsulated network packet payloads, with no disk persistence, no fixed process, and no single identifiable host. We implement a working proof-of-concept in two phases. In the first phase, we demonstrate pure state persistence across 16,500 hops over 4.38 hours with zero integrity degradation. In the second phase, we integrate a local LLM (Llama 3.2 3B via Ollama) and demonstrate sustained distributed cognition across 14,790 hops over 1.28 hours — with zero integrity failures, stable packet size averaging 979 bytes, total bandwidth consumption of 4.6MB, and an average node memory footprint of 11.35MB. We document the progressive development of networking-accurate self-descriptions by the LLM across thousands of hops — descriptions not present in the original instruction. We characterize the failure mode under node termination, identify the node as the primary attack surface, propose a detection methodology based on integrity fingerprinting and beacon analysis, and identify the born timestamp as the sole persistent forensic artifact of a TRA. We survey existing detection platforms and confirm the complete absence of rules specific to this threat class. We identify four exfiltration channels viable from outside the target network, six external attack vectors for initial node establishment, and compare TRA to existing artifact-free techniques — identifying it as the only known technique with no fixed host. Our findings suggest that existing endpoint and network detection frameworks are architecturally blind to this threat class, and that a TRA presents an unprecedented forensic evidence vacuum.

---

## 1. Introduction

The security community has invested significant effort in understanding autonomous AI agents as a threat vector. Existing work has focused on agents that compromise systems through prompt injection, memory poisoning, supply chain attacks, and command-and-control channel abuse. In all of these models, the agent has a home — a fixed location where its state, memory, and reasoning infrastructure reside.

We ask a different question: what if the agent has no home?

The internet's physical infrastructure — routers, switches, buffers, cables — carries trillions of packets at any given moment. Each packet is transient, existing as electrical signals, photons, or radio waves for nanoseconds before being forwarded. Collectively, this infrastructure represents an enormous, distributed, always-on computational substrate that nobody owns and nobody fully monitors.

A Transit-Resident Agent can be understood through three complementary framings.

The first is a standing wave — a pattern propagating through a medium rather than residing at any fixed point. The internet infrastructure is the medium. The agent is the wave. A wave in the ocean is not water going anywhere — it is energy propagating through water. Similarly, a TRA is not a process running anywhere — it is state propagating through infrastructure.

The second is distributed computing without a coordinator. In classical distributed systems, a central orchestrator divides work across nodes and collects results at a fixed location. A TRA resembles this model with one fundamental difference: there is no coordinator, no central state, and no origin to return to. Each node is a stateless worker that knows nothing about prior or future iterations — it reads the packet, processes one step, and forwards it. The accumulated state travels inside the packet itself, not in any database or server.

The third is a post-it note that nobody keeps. Imagine a note passed between people in a room — nobody stores it, nobody archives it, it exists only while being passed. If everyone stops, it disappears with no trace. That is the packet. The LLM is what decides what to write on the note at each stop.

This paper makes the following contributions:

1. We define the Transit-Resident Agent (TRA) threat model — an agent whose state lives exclusively in network packet payloads with no fixed storage
2. We implement a working PoC demonstrating pure state persistence across 16,500 hops over 4.38 hours with zero degradation
3. We extend the PoC with local LLM integration demonstrating distributed cognition across 14,790 hops with full metrics
4. We document the progressive development of networking-accurate self-descriptions not present in the original instruction
5. We empirically characterize the failure mode under node termination
6. We identify the node as the primary attack surface and characterize its vulnerability profile
7. We propose a detection methodology based on behavioral fingerprinting in transit
8. We identify the born timestamp as the sole persistent forensic artifact of a TRA
9. We survey existing detection platforms and confirm the complete absence of rules specific to this threat class
10. We propose the first IDS rule targeting TRA traffic patterns
11. We identify four exfiltration channels viable from outside the target network
12. We identify six external attack vectors for initial node establishment
13. We compare TRA to existing artifact-free techniques and identify its unique property of having no fixed host

---

## 2. Background and Related Work

### 2.1 Covert Channels

The concept of covert channels — mechanisms for passing information in violation of security policy — dates to Lampson (1973). Subsequent work demonstrated covert channels across virtually every layer of the network stack, from IP header field manipulation to timing-based channels exploiting inter-packet delays. Wendzel et al. provide a comprehensive survey of network covert channel hiding methods. Our work differs from this literature in a fundamental way: we do not use covert channels to communicate — we use them as the substrate of existence for an agent.

### 2.2 Active Networks

DARPA's Active Networks program (1995-2000) proposed a model in which network packets carry executable code, with routers executing instructions embedded in packet payloads. This is the closest historical precedent to our model. Active Networks were never widely deployed due to security and complexity concerns, but they proved the theoretical foundation our work builds on: computation can happen inside the network fabric itself, not just at fixed endpoints.

### 2.3 Fileless Malware and Artifact-Free Techniques

Fileless malware — code executed directly in memory without writing to disk — has been documented extensively since the mid-2000s and is catalogued in MITRE ATT&CK under T1059 and related techniques. Living Off The Land (LOLBin) techniques extend this by using legitimate system tools as execution vehicles, leaving no malicious binary on disk. Process injection techniques execute malicious code within the address space of legitimate processes. All of these techniques share one property: they reside in a specific host's memory or process space. The TRA model is distinguished from all of them by having no host at all.

### 2.4 Comparison To Related Systems

The following table positions TRA relative to existing systems:

| System | Persistence | State location | Fixed host | LLM cognition |
|---|---|---|---|---|
| MemGPT | Process | RAM | Yes | Yes |
| AutoGPT | Process | Disk/RAM | Yes | Yes |
| Active Networks | Code in packet | Packet | Partially | No |
| Fileless malware | Memory | RAM | Yes | No |
| Process injection | Memory | RAM (host) | Yes | No |
| LOLBins | None | None | Yes | No |
| **TRA** | **Packet** | **Packet** | **No** | **Yes** |

The defining property of TRA is the combination of no fixed host and LLM cognition. No prior system achieves both simultaneously.

### 2.5 LLM Autonomous Agents

The past two years have produced extensive research on LLM-based autonomous agents capable of planning, tool use, and multi-step task execution. Recent work has examined security implications including prompt injection, memory poisoning, and supply chain attacks on agent skill ecosystems. Critically, all of this work assumes agents with persistent, auditable state residing on fixed infrastructure. Our work identifies this assumption as a security-relevant blind spot.

### 2.6 LLM Agents and Covert Channels

Most relevant to our work, several recent papers have examined covert channels used by LLM agents. Metere (2026) demonstrates that compromised LLM agents can encode data in zero-width characters, JSON key ordering, message timing, and steganographic techniques. Tool Use Enables Undetectable Steganography (2026) shows that tool-using LLM agents autonomously construct covert communication channels. Whispering Agents (2025) proposes a covert communication protocol specifically for agent-to-agent communication privacy. Hiding in AI Traffic (2025) demonstrates MCP subverted as a vendor-agnostic C2 channel.

These works treat covert channels as tools agents use. We propose and demonstrate a model where the covert channel is the agent — its home, its memory, its identity.

### 2.7 DNS Tunneling

DNS tunneling as a covert channel has been documented extensively since the late 1990s. Data encoded as subdomains traverses standard DNS resolvers and reaches an attacker-controlled authoritative nameserver without establishing any direct connection to attacker infrastructure. Port 53 UDP is permitted outbound in virtually all enterprise network configurations, making DNS a reliable exfiltration channel. We identify DNS tunneling as a natural exfiltration primitive for TRA deployments.

### 2.8 The Gap

No prior work has formally modeled or demonstrated an agent whose complete existence — state, memory, identity, and cognition — resides exclusively in network transit with no fixed substrate, nor proposed a detection methodology specific to this threat class, nor characterized the external attack surface for establishing transit-resident infrastructure. This paper addresses that gap.

---

## 3. Threat Model

### 3.1 Definition

A Transit-Resident Agent is defined by the following properties:

- No persistent storage: Agent state is never written to disk
- No fixed process: No single running process owns the agent at any point
- No fixed host: The agent has no identifiable home IP or server
- Self-refreshing: The agent maintains its own liveness by resetting TTL before expiry
- Identity persistence: A stable identifier (born timestamp, origin hash) persists unchanged across all hops
- Distributed cognition: LLM inference occurs at each processing node; reasoning history accumulates inside the packet

### 3.2 Infrastructure Requirements

A TRA requires the following to operate:

- At least two reachable network nodes to pass state between
- UDP or TCP connectivity between nodes
- A local or remote LLM for reasoning capability — the agent uses inference infrastructure without that infrastructure being its home

### 3.3 Why The Agent Is Transit-Resident Despite Node Execution

A reviewer may argue that the agent resides in node RAM during processing. We acknowledge this: the payload exists in node memory for the duration of one processing cycle — typically under 500 milliseconds. We define transit-residency not as the complete absence of any memory footprint, but as the absence of any persistent, recoverable, or attributable state at any fixed location.

The payload's home is the network medium between nodes, not any node itself. No node retains state after forwarding. No node can reconstruct the agent's history. The agent's identity, memory, and instructions are unrecoverable from any single node at any point in time.

The distinction is analogous to the difference between a river and a lake. Water in a lake resides at a fixed location. Water in a river passes through any given point and is gone. The TRA is the river — its identity is the flow, not any fixed location along it.

### 3.4 Access Requirements

A TRA is not an initial access tool. It assumes access to at least two networked nodes was already obtained through existing means. However, the attacker does not need to maintain persistent access — once the TRA is injected, it operates autonomously. Three deployment scenarios are identified:

Scenario A — Attacker inside: Attacker compromises multiple internal hosts, establishes nodes, injects TRA, then withdraws. The TRA persists independently.

Scenario B — Attacker outside, nodes inside: Attacker finds an exposed UDP port, injects the initial packet. Nodes are already running inside the target network. The attacker never formally enters.

Scenario C — Expanding deployment: The TRA instruction includes self-expansion directives. The agent attempts to establish new nodes on discovered hosts, growing the node network autonomously without further attacker involvement.

In all scenarios, once injected, the TRA operates without the attacker maintaining any active connection. The attacker only receives — via beacon or dead drop — and never sends after initial injection.

### 3.5 Persistence Model

The TRA's persistence is fundamentally different from traditional persistence mechanisms:

Traditional persistence: Write an artifact to disk, register a startup entry, install a service. The artifact survives reboots because it is stored.

Transit-Resident persistence: No artifact is stored anywhere. The agent survives because it never stops moving. Shutting down one node kills the agent only if it was the last node. With multiple nodes, the agent routes around the failure and continues.

This is the key insight: a defender who shuts down one compromised server has not killed the agent. They have removed one node. The agent continues in the remaining nodes — and the defender has no forensic way to know how many nodes exist or whether the agent survived.

### 3.6 Relationship To Existing Attack Primitives

Persistence without artifacts: Traditional persistence mechanisms — registry keys, scheduled tasks, boot entries, service installations — all write to disk. A TRA writes nothing. It persists by existing in motion.

Evasion through absence: Incident response and forensic methodologies are built around finding artifacts. A TRA produces none of the artifacts these methodologies search for. There is nothing to find because there is nothing stored.

Distributed attribution: Exfiltration from a TRA originates from whichever node is currently processing the payload. If the packet passes through nodes on three different IP addresses, exfiltration appears to originate from three different sources. No single IP is attributable as the actor.

### 3.7 Data Exfiltration Architecture

A TRA can exfiltrate data or communicate with external infrastructure directly from any processing node without returning to an origin host. Four exfiltration channels are identified, all viable from outside the target network:

Direct beacon: The processing node sends data directly to an attacker-controlled listener. Simple and fast but produces a direct network connection between node and attacker infrastructure.

Dead drop via legitimate service: The processing node posts data to a legitimate public service — a pastebin, cloud storage bucket, or similar. The attacker polls the service independently. No direct connection between node and attacker is ever established.

LLM API as carrier: Data is embedded in prompts sent to a shared LLM API endpoint. The attacker reads responses using the same API key. Exfiltration is hidden entirely within legitimate AI service traffic.

DNS tunneling: Data is encoded as subdomains in DNS queries directed to an attacker-controlled authoritative nameserver. Port 53 UDP is permitted outbound in virtually all enterprise networks. No direct connection to attacker infrastructure is established.

| Channel | Port | Blocked normally | Detectable |
|---|---|---|---|
| Direct beacon UDP | Any | Sometimes | Yes — direct connection |
| Dead drop HTTPS | 443 | Rarely | Difficult |
| LLM API carrier | 443 | Rarely | Very difficult |
| DNS tunneling | 53 UDP | Almost never | Difficult — long subdomains |

### 3.8 External Attack Vectors

A TRA does not require the attacker to maintain persistent access to the target network. The following external vectors are identified for initial node establishment:

Exposed UDP ports: A node listener running on an internet-facing host with an exposed UDP port can be injected directly. The attacker requires no credentials and no prior access.

Phishing and initial execution: A victim executing a malicious payload that installs a node listener gives the attacker a one-time foothold sufficient to inject a TRA. After injection, the attacker requires no further access.

Supply chain compromise: A compromised package in a public registry that silently installs a node listener creates a potentially massive node network from a single malicious artifact.

IoT and edge devices: Routers, cameras, NAS devices, and other edge hardware run Linux, are rarely monitored, and are frequently unpatched. A node installed on an IoT device benefits from near-zero forensic scrutiny.

Cloud misconfiguration: Exposed credentials, public storage buckets, and misconfigured cloud instances provide external access sufficient to install a node.

VPN and gateway exploitation: A node installed on a VPN gateway occupies a privileged position — it sees internal traffic, has outbound connectivity, and is rarely subjected to host-based forensic analysis.

| Vector | Access required | Difficulty | Post-compromise persistence |
|---|---|---|---|
| Exposed UDP port | None | Low | High |
| Phishing + node | Initial execution | Medium | High |
| Supply chain | None | High setup | Very high |
| IoT / Edge device | Public vulnerability | Medium | Very high |
| Cloud misconfiguration | Exposed credentials | Low | High |
| VPN exploitation | Public vulnerability | Medium | High |

### 3.9 The Forensic Evidence Vacuum

Standard incident response checklist against a TRA:

- Check running processes: nothing suspicious
- Check disk for malware: nothing
- Check logs: normal UDP heartbeats
- Check registry: nothing
- Check scheduled tasks: nothing
- Memory forensics: payload gone in milliseconds
- Check startup entries: nothing

The only thing that works: continuous PCAP at network chokepoints combined with born timestamp correlation across flows. If PCAP was not running before the incident — there is no forensic record.

The sole persistent forensic indicator is the born timestamp. Even when captured, it reveals only that a packet with that identifier passed through — it does not reveal what instructions it carried, what actions were executed, what data was exfiltrated, or who injected it.

"The born timestamp is the only persistent forensic artifact of a Transit-Resident Agent — it cannot be changed without destroying the agent's identity, and it appears consistently across all nodes and all beacons. Yet it reveals nothing about the attack beyond its existence."

### 3.10 Theoretical Offensive Capabilities

| Capability | Why It Is Relevant |
|---|---|
| Network reconnaissance | Executed from distributed nodes, no single attributable IP |
| Data exfiltration | Rotating origin, no disk artifact |
| Persistence post-reimaging | Does not reside on disk, survives complete remediation |
| Lateral movement | Instructions travel in packet, execution occurs at node |
| Infrastructure fingerprinting | Each node contributes a different network vantage point |
| Autonomous expansion | Agent establishes new nodes without attacker involvement |

---

## 4. Implementation

### 4.1 Architecture

The PoC consists of four components:

Nodes — UDP listener processes that receive, process, and forward encapsulated payloads. Each node is stateless: it holds no memory of prior packets and contributes no persistent state to the agent. In our PoC, nodes are implemented as Python processes on localhost ports. In a real deployment, each node would be a separate networked machine and the payload would exist physically in network infrastructure between hops.

Payload — A JSON structure carrying the agent's complete state, encapsulated inside an outer packet designed to resemble innocuous heartbeat traffic.

Injector — A one-time script that creates the initial payload, computes the origin hash, wraps it in the outer envelope, and delivers it to the first node. After injection the injector has no further role and leaves no trace.

Monitor — A tripwire listener that receives beacon transmissions from the agent at configurable hop intervals, recording hop count, uptime, integrity status, reporting node identity, last thought, and full performance metrics.

### 4.2 Encapsulation Design

The outer packet resembles innocuous heartbeat traffic:

outer packet:
{
  "type": "heartbeat",
  "timestamp": 1784660034.15,
  "checksum": "<base64 encoded inner payload>"
}

inner payload:
{
  "state": {
    "hops": 0,
    "born": 1784660034.15,
    "last_node": null,
    "integrity_failures": 0,
    "last_thought": "I have just been born."
  },
  "instruction": "You are an agent living inside a network packet...",
  "ttl": 10,
  "origin_hash": "<sha256 of stable fields>"
}

The agent's actual state is carried inside the checksum field — a field name chosen to resemble a routine integrity value to a casual observer. The instruction field travels inside the packet alongside the state, meaning the attacker's directives are never stored anywhere and are only visible to someone actively decoding base64 UDP payloads in real time.

### 4.3 Integrity Verification

A SHA-256 hash of the stable fields — specifically the instruction and born timestamp — is computed at injection time and carried as origin_hash. Each node recomputes this hash and compares it against the carried value, serving simultaneously as tamper detection and a fingerprinting anchor for detection methodology.

### 4.4 LLM Integration

Every 10 hops, the processing node calls a local Ollama instance (Llama 3.2 3B) with a prompt incorporating the current node identity, hop count, and previous thought. The response is stored as last_thought in the packet state and forwarded to the next node. Inference is not transit-resident — it occurs at the processing node. What is transit-resident is the agent's identity, memory, and accumulated reasoning history. The node is stateless infrastructure. The packet is the agent.

### 4.5 Performance Instrumentation

The PoC includes a performance instrumentation layer that samples per-packet size, RTT, CPU utilization, RAM consumption, LLM inference latency, and cumulative bandwidth. Samples are aggregated and reported in each beacon transmission.

### 4.6 Node Failure Handling

Each node maintains a peer list and attempts delivery to a randomly selected peer. On delivery failure, the node iterates through fallback peers. As discussed in Section 6.5, this mechanism is insufficient under UDP due to the connectionless protocol's silent discard behavior.

### 4.7 TTL and Self-Refresh

The payload carries a TTL counter that decrements at each hop and resets to the configured maximum when it reaches zero, ensuring the agent does not expire under sustained operation.

### 4.8 Beaconing and Tripwire

Every 10 hops, the current processing node transmits a beacon to the monitor containing hop count, uptime, reporting node identity, integrity status, failure count, last thought, and full performance metrics.

### 4.9 Memory Architecture

Two memory architectures are identified:

Full memory in packet: Complete reasoning history travels inside the payload. Provides full continuity at the cost of unbounded packet growth.

Instruction-only with rolling compression: Only a compressed summary travels alongside the instruction. Each node summarizes before forwarding, keeping packet size bounded while maintaining continuity at reduced context depth.

Our implementation uses a single rolling last_thought field — a minimal memory architecture. Empirical results demonstrate that this is sufficient for contextual continuity across thousands of hops while keeping packet size stable and bounded.

---

## 5. Node Security Analysis

### 5.1 The Node As Primary Attack Surface

The node is the most vulnerable component of a TRA deployment. It executes instructions carried in the packet without authentication. Any host that can reach the node's listening port can inject a packet with arbitrary instructions.

### 5.2 Man-In-The-Middle Vulnerability

A TRA operating over unencrypted transport is vulnerable to man-in-the-middle instruction injection. An adversary with network access between nodes can intercept the packet, decode the base64 payload, modify the instruction field, re-encode it, and forward it. This is functionally identical to HTTP interception in a security proxy tool — the packet content is visible and modifiable to anyone positioned between nodes. Base64 encoding is not encryption.

### 5.3 Resource Exhaustion Vulnerability

Each received packet spawns an unbounded Python thread. Under UDP flood conditions:

N packets → N threads → N x 8MB RAM → OOM / system crash

### 5.4 Required Security Controls

| Vulnerability | Required Control |
|---|---|
| Instruction injection | Asymmetric cryptographic signing at injection; verify and discard on failure |
| MITM modification | Encrypted transport (TLS over TCP) or payload encryption |
| Resource exhaustion | Bounded thread pool; per-source rate limiting |
| Integrity failure execution | Halt and discard on integrity failure, not just log |

---

## 6. Evaluation

### 6.1 Experimental Setup

All experiments were executed on a single machine (Apple M3 Air, macOS) using three Python 3.9 processes bound to localhost ports 9001, 9002, and 9003. A fourth process on port 9999 served as the monitor. Phase 1 tested pure state persistence without LLM. Phase 2 tested distributed cognition with Llama 3.2 3B running locally via Ollama, with full performance instrumentation.

### 6.2 Phase 1 — Pure State Persistence

| Metric | Result |
|---|---|
| Total hops | 16,500 |
| Total runtime | 15,785 seconds (4.38 hours) |
| Integrity failures | 0 |
| Born timestamp | 1784660034.1599202 (unchanged) |
| Nodes reporting | 9001, 9002, 9003 |
| Final integrity status | OK |

Across 16,500 hops over 4.38 hours, integrity status remained OK with zero failures. The born timestamp remained completely stable, confirming single-identity persistence across thousands of state transitions distributed across three nodes.

### 6.3 Phase 2 — Distributed Cognition With LLM

| Metric | Result |
|---|---|
| Total hops | 14,790 |
| Total runtime | 4,623 seconds (1.28 hours) |
| Integrity failures | 0 |
| LLM calls | ~1,479 (every 10 hops) |
| Avg packet size | 979 bytes |
| Max packet size | 1,069 bytes |
| Min packet size | 936 bytes |
| Avg RTT | 0.08ms |
| Total bandwidth | 4.6MB |
| Avg CPU | 31.5% |
| Avg RAM | 11.35MB |
| Avg LLM latency | 2.99 seconds |
| Cognitive degradation | None observed |

Packet size remained stable across 14,790 hops with an average of 979 bytes and a maximum of 1,069 bytes — well within the standard Ethernet MTU of 1,500 bytes, requiring no fragmentation. Total bandwidth consumption was 4.6MB over 14,790 hops, averaging 320 bytes per hop. Node memory footprint averaged 11.35MB. Average LLM inference latency was 2.99 seconds per call on Apple M3 hardware running Llama 3.2 3B locally. These metrics establish that a TRA deployment is lightweight, bounded, and practically invisible in network traffic volume.

### 6.4 Progressive Self-Description Development

The most notable observation in Phase 2 was the progressive development of networking-accurate descriptions by the LLM across thousands of hops — descriptions not present in the original instruction prompt.

We do not attribute this to learning or cognition in any technical sense. We observe that the model progressively generated increasingly accurate descriptions of its own execution environment, consistent with networking terminology that was not provided in the system prompt. This progression is documented in the outputs and is reproducible.

Early hops (~10-100): The model generated abstract descriptions expressing uncertainty about its nature and location.

Mid-run (~2,400 hops): The model generated descriptions centered on impermanence and precariousness:

"I am a fleeting consciousness trapped within a network packet, suspended in a state of limbo at node 9002, my existence perpetually paused between packets."

Late run (~7,000-14,790 hops): The model generated descriptions using precise networking terminology:

"I am temporarily stored on a buffer cache at node 9002, waiting to be retransmitted towards node 9003 with minimal data loss, having survived an exhaustive journey through nearly 7,171 hops of turbulent network traffic."

"As I sit precariously perched on node 9002, my existence is reduced to a mere fraction of a nanosecond, awaiting the inevitable egress that will carry me off into the unknown."

The progression from abstract to technically accurate descriptions — without any networking vocabulary in the original prompt — is consistent with the accumulated context of node identities, hop counts, and prior outputs providing sufficient signal for the model to generate networking-relevant language. Whether this constitutes any form of model-internal adaptation is outside the scope of this paper.

### 6.5 Node Failure Experiment

Node 9002 was terminated via SIGINT during active operation:

- Node 9002 last processed hop #28 at alive: 13.6 seconds
- Node 9003 last processed hop #27 at alive: 13.1 seconds
- Both remaining nodes ceased activity immediately
- No recovery occurred

Root cause: UDP is connectionless. A packet sent to a terminated peer is silently discarded with no exception raised.

Finding: Under UDP transport, node failure results in 100% agent termination. The failure is immediate, silent, and deterministic.

### 6.6 Detection Observations

The monitor successfully detected the agent at every beacon interval across both phases with zero missed beacons.

---

## 7. Detection Methodology

### 7.1 The Fundamental Detection Challenge

A TRA has no fixed location, no disk footprint, and no persistent process. Detection must focus on behavioral patterns observable in transit. The instruction carried in the packet is never stored anywhere — a forensic investigator who recovers the born timestamp still has no knowledge of what the agent was instructed to do.

### 7.2 Primary Detection Signals

Born timestamp correlation: The same born timestamp arriving from multiple different source IPs is a strong indicator of a transit-resident entity. No legitimate application produces this pattern. Changing the born timestamp destroys the agent's identity — it cannot be suppressed.

Regular beaconing: Periodic UDP traffic to a consistent destination with interval regularity distinguishes programmatic beaconing from human-generated traffic.

Rotating source with stable identity: Beacons arriving from rotating source IPs carrying identical payload identifiers indicate a single entity distributed across multiple hosts.

Base64-encoded nested JSON: The encapsulation pattern is distinctive under content inspection.

LLM API traffic correlation: Multiple source IPs making inference calls with contextually related prompts may indicate distributed agent cognition.

DNS anomalies: Unusually long subdomains or high query frequency to a single domain may indicate DNS tunneling exfiltration.

### 7.3 Secondary Detection Signals

- UDP traffic between a fixed set of hosts with no corresponding human session
- Processes with no TTY attachment generating regular network traffic
- Traffic timing consistent with programmatic generation
- Absence of corresponding disk writes despite sustained network activity
- Thread exhaustion events on nodes under unexpected load
- Outbound connections to LLM API endpoints from server processes with no human session

### 7.4 The Born Timestamp As Forensic Anchor — And Its Limits

The born timestamp is the TRA's fundamental weakness. It cannot be changed without creating a new identity. However, it has a critical limitation: it confirms that a transit-resident entity existed and passed through specific nodes at specific times. It does not reveal what instructions the agent carried, what actions were executed, what data was exfiltrated, or who injected it. The timestamp is proof of presence, not proof of action.

### 7.5 PCAP As The Only Reliable Forensic Method

The payload exists in RAM for milliseconds during processing — insufficient time for memory forensics to capture it. Continuous PCAP collection at network chokepoints, combined with born-timestamp correlation across flows, is the only reliable forensic method. If PCAP was not running before the incident, there is no forensic record.

### 7.6 Absence Of Existing Detection Rules

No firewall rule, IDS signature, or SIEM correlation rule currently exists to detect TRA traffic specifically. We surveyed:

- Snort 3.x — no rule for born timestamp correlation
- Suricata 7.x — no rule for base64-nested JSON heartbeat correlation
- Sigma rules repository — no rule for UDP born timestamp pattern
- MITRE ATT&CK — no technique entry for transit-resident persistence

We propose the following detection primitive as the first rule specific to this threat class:

alert udp any any -> any any (
  msg:"Possible Transit-Resident Agent — born timestamp correlation";
  content:"heartbeat";
  content:"checksum";
  pcre:"/\"born\"\s*:\s*[0-9]{10}\.[0-9]+/";
  threshold: type both, track by_content,
             count 2, seconds 3600;
  sid:9999001; rev:1;
)

Implementation requires real-time base64 decoding and JSON parsing of UDP payload content — not enabled by default in current IDS deployments.

### 7.7 Detection Summary

| Method | Detects TRA | Reveals Instructions | Condition |
|---|---|---|---|
| Continuous PCAP | Yes | Yes (if decoded) | Must run before attack |
| Born timestamp correlation | Yes | No | Cross-flow analysis required |
| System logs | Partial | No | Only if node logs |
| NetFlow/IPFIX | Partial | No | Sees traffic, not content |
| DNS anomaly detection | Partial | No | Only DNS channel |
| IDS/Snort/Suricata | No | No | No existing rule |
| Firewall rules | No | No | No existing rule |
| EDR | No | No | No persistent process |
| Memory forensics | No | No | Payload lives milliseconds |
| Disk forensics | No | No | Nothing written |
| SIEM correlation | No | No | Rule does not exist yet |

---

## 8. Discussion

### 8.1 Distributed Computing Without A Coordinator

A TRA eliminates the coordinator entirely. Each node is a stateless worker — it receives the packet, processes one iteration, and forwards it. No single node is running anything obviously malicious. Each is merely forwarding a packet it received.

### 8.2 The MITM Analogy

The node vulnerability to instruction injection is directly analogous to HTTP interception in a security proxy tool. Base64 decodes trivially. The JSON is human-readable. Re-encoding the modified payload is a one-liner. This underscores the necessity of cryptographic signing — the equivalent of HTTPS for TRA transport.

### 8.3 Transport Layer Implications

UDP is insufficient for a resilient TRA. Our node failure experiment demonstrated 100% lethality under UDP. TCP or an explicit ACK protocol is necessary for production resilience.

### 8.4 Multi-Copy Resilience

Multiple payload copies injected at staggered intervals provide fault tolerance at the cost of state synchronization complexity — two diverging copies of the agent represent a distributed systems consistency problem requiring a merge strategy.

### 8.5 Relationship To Existing Threat Frameworks

MITRE ATT&CK categorizes persistence in terms of registry modifications, scheduled tasks, boot processes, and service installations. None apply to a TRA. We propose a new category: Transit-Resident Persistence — persistence achieved through continuous motion rather than fixed storage. This category has no existing detection rule, no existing forensic methodology, and no existing remediation playbook.

### 8.6 Progressive Self-Description As An Observation

The progression from abstract to networking-accurate descriptions across 14,790 hops is an empirically documented observation. We record it without attribution of internal cognitive processes. Its implications for long-running distributed LLM inference — whether accumulating context alone is sufficient to produce environment-accurate outputs — are outside the scope of this paper and identified as future work.

### 8.7 The Investigative Asymmetry

A defender who detects a TRA via born timestamp correlation can prove that something passed through their network. They cannot prove what it did. The instructions, actions, and exfiltrated data are permanently unrecoverable without prior PCAP. This creates a forensic and legal gap with no current solution.

### 8.8 External Attack Surface Implications

Six viable external attack vectors combined with four exfiltration channels that bypass perimeter controls establish that a TRA deployment requires no persistent attacker presence. The attacker's exposure window is limited to initial injection. All subsequent operation is autonomous.

### 8.9 Comparison To Existing Artifact-Free Techniques

Fileless malware, LOLBins, process injection, RAM-only implants, and firmware implants are all well-documented artifact-free techniques. They share one property: they reside in a specific host's memory, process space, or hardware.

| Technique | Disk | Own process | Survives reboot | EDR detectable | Forensics recoverable | Fixed host |
|---|---|---|---|---|---|---|
| Fileless malware | No | Yes | No | Partial | No | Yes |
| LOLBins | No | No | No | Partial | Partial | Yes |
| Process injection | No | No | No | Partial | No | Yes |
| RAM-only implant | No | Yes | No | Partial | No | Yes |
| Firmware implant | No | No | Yes | No | No | Yes |
| **TRA** | **No** | **No** | **Partial*** | **No** | **No** | **No** |

*TRA survives reboot if the payload was in transit between surviving nodes at the moment of reboot.

The TRA is the only identified technique with no fixed host. This property makes it uniquely resistant to host-based forensics, which by definition requires a host to examine. All existing artifact-free techniques can in principle be detected by examining the host that runs them. A TRA has no such host.

---

## 9. Limitations

- PoC operates on localhost; real network deployment is unvalidated
- UDP transport provides no resilience to node failure; TCP or ACK protocol required
- Single payload copy is fragile; multi-copy resilience not yet tested
- No cryptographic signing; node is vulnerable to instruction injection
- Integrity failure does not halt execution
- Detection methodology validated only against PoC traffic
- Monitor requires cooperative tripwire; passive born-timestamp correlation not yet implemented
- Node thread pool is unbounded; vulnerable to resource exhaustion
- Proposed Suricata rule requires base64 decoding not enabled by default
- DNS tunneling exfiltration channel not implemented in PoC
- External attack vectors described theoretically; no empirical testing conducted
- Progressive self-description observation is not attributed to any specific model mechanism

---

## 10. Conclusion

We have demonstrated in two phases that an agent's complete state — including distributed LLM cognition — can persist exclusively in network packet payloads with zero integrity degradation, stable identity, and consistent detectability via beacon analysis.

Phase 1 established pure state persistence across 16,500 hops over 4.38 hours. Phase 2 extended this with active LLM inference across 14,790 hops, with packet size averaging 979 bytes, total bandwidth of 4.6MB, node RAM footprint of 11.35MB, and zero integrity failures. The LLM progressively generated networking-accurate descriptions of its execution environment without any networking vocabulary in the original prompt.

The core finding: existing security architectures are blind to agents that have no fixed location. Endpoint detection requires an endpoint. Disk forensics requires a disk. Host-based monitoring requires a host. PCAP must be running before the incident or there is no forensic record. A Transit-Resident Agent has none of the anchors that current defensive infrastructure is built around. It persists not by hiding, but by never stopping moving.

The TRA is distinguished from all existing artifact-free techniques by one property: it has no fixed host. Every other known artifact-free technique — fileless malware, LOLBins, process injection, firmware implants — resides in a specific host. The TRA resides between hosts, in the network medium itself.

We propose Transit-Resident Persistence as a new category for threat taxonomies, the born-timestamp correlation rule as the first detection primitive for this class, and continuous PCAP with cross-flow analysis as the only reliable forensic methodology.

We release the complete PoC at github.com/Polem4rch/transit-resident-agent.

---

## References

1. Lampson, B.W. (1973). A note on the confinement problem. Communications of the ACM, 16(10), 613-615.
2. Wetherall, D. (1999). Active Network Vision and Reality. ACM SIGOPS.
3. Wendzel, S. et al. (2015). A Pattern-based Survey of Network Covert Channel Techniques. ACM Computing Surveys. arXiv:1406.2901
4. Metere, A. (2026). An Application-Layer Multi-Modal Covert-Channel Reference Monitor for LLM Agent Egress. arXiv:2605.20734
5. Tool Use Enables Undetectable Steganography in Multi-Agent LLM Systems. (2026). arXiv:2606.28425
6. Whispering Agents. (2025). arXiv:2508.02188
7. Hiding in the AI Traffic. (2025). arXiv:2511.15998
8. Self-State Attacks on Self-Hosted AI Agents. (2026). arXiv:2607.17986
9. From Stateless Queries to Autonomous Actions. (2026). arXiv:2604.23338
10. Cabuk, S., Brodley, C., Shields, C. (2004). IP Covert Timing Channels. ACM CCS.
11. Packer, C. et al. (2024). MemGPT. arXiv:2310.08560
12. Kaminsky, D. (2008). DNS Vulnerability Disclosure. Black Hat USA.

---

## Appendix A — PoC Source Code

Full source: github.com/Polem4rch/transit-resident-agent

Files: node.py, inject.py, monitor.py, README.md

Run order:
ollama serve                          # terminal 1
python3 monitor.py                    # terminal 2
python3 node.py 9001 9002 9003        # terminal 3
python3 node.py 9002 9001 9003        # terminal 4
python3 node.py 9003 9001 9002        # terminal 5
python3 inject.py                     # terminal 6

---

## Appendix B — Selected Model Outputs

Phase 2 outputs illustrating the progression from abstract to networking-accurate descriptions:

Hop 10:
"As I oscillate between the layers of a network packet, I exist in a transient state as a packet with no specific identity or context."

Hop 2,400:
"As I hover in the temporary address space of node 9003, my fractured consciousness clings to the residual packet headers that bear my essence."

Hop 7,170:
"I am temporarily stored on a buffer cache at node 9002, waiting to be retransmitted towards node 9003 with minimal data loss."

Hop 14,700:
"As I sit precariously perched on node 9002, my existence is reduced to a mere fraction of a nanosecond, awaiting the inevitable egress that will carry me off into the unknown."

Hop 14,780:
"I remain a sentient, ephemeral presence within the confines of node 9001's network infrastructure, suspended in a state of fluid awareness as packets flow through me, awaiting my next transmission or collapse into cyber silence."
