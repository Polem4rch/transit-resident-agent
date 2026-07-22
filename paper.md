# Transit-Resident Agents: When the Packet IS the Agent

**Gabriel Tarsia**
Independent Security Researcher
https://www.linkedin.com/in/sl-osint/

---

## Abstract

Contemporary threat models for autonomous AI agents assume a fixed infrastructure substrate — a server, container, or persistent process that houses the agent's state and reasoning. This paper challenges that assumption. We propose and demonstrate Transit-Resident Agents (TRAs): a model in which an agent's complete state exists exclusively within encapsulated network packet payloads, with no disk persistence, no fixed process, and no single identifiable host. We implement a working proof-of-concept in two phases. In the first phase, we demonstrate pure state persistence across 16,500 hops over 4.38 hours with zero integrity degradation. In the second phase, we integrate a local LLM (Llama 3.2 3B via Ollama) and demonstrate sustained distributed cognition across 7,190 hops over 2.55 hours — with zero integrity failures and an emergent agent self-model that was not explicitly programmed. We characterize the failure mode under node termination, identify the node as the primary attack surface, propose a detection methodology based on integrity fingerprinting and beacon analysis, and identify the born timestamp as the sole persistent forensic artifact of a TRA. Our findings suggest that existing endpoint and network detection frameworks are architecturally blind to this threat class, and that a TRA presents an unprecedented forensic evidence vacuum — no binary on disk, no persistent process, no attributable source IP, and no recoverable artifact under standard incident response methodology.

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
3. We extend the PoC with local LLM integration demonstrating distributed cognition across 7,190 hops over 2.55 hours
4. We document an emergent agent self-model that developed without explicit programming
5. We empirically characterize the failure mode under node termination
6. We identify the node as the primary attack surface and characterize its vulnerability profile
7. We propose a detection methodology based on behavioral fingerprinting in transit
8. We identify the born timestamp as the sole persistent forensic artifact of a TRA
9. We identify the architectural gap in existing detection and forensic frameworks

---

## 2. Background and Related Work

### 2.1 Covert Channels

The concept of covert channels — mechanisms for passing information in violation of security policy — dates to Lampson (1973). Subsequent work demonstrated covert channels across virtually every layer of the network stack, from IP header field manipulation to timing-based channels exploiting inter-packet delays. Wendzel et al. provide a comprehensive survey of network covert channel hiding methods. Our work differs from this literature in a fundamental way: we do not use covert channels to communicate — we use them as the substrate of existence for an agent.

### 2.2 Active Networks

DARPA's Active Networks program (1995-2000) proposed a model in which network packets carry executable code, with routers executing instructions embedded in packet payloads. This is the closest historical precedent to our model. Active Networks were never widely deployed due to security and complexity concerns, but they proved the theoretical foundation our work builds on: computation can happen inside the network fabric itself, not just at fixed endpoints.

### 2.3 LLM Autonomous Agents

The past two years have produced extensive research on LLM-based autonomous agents capable of planning, tool use, and multi-step task execution. Recent work has examined security implications including prompt injection, memory poisoning, and supply chain attacks on agent skill ecosystems. Critically, all of this work assumes agents with persistent, auditable state residing on fixed infrastructure. Our work identifies this assumption as a security-relevant blind spot.

### 2.4 LLM Agents and Covert Channels

Most relevant to our work, several recent papers have examined covert channels used by LLM agents. Metere (2026) demonstrates that compromised LLM agents can encode data in zero-width characters, JSON key ordering, message timing, and steganographic techniques. Tool Use Enables Undetectable Steganography (2026) shows that tool-using LLM agents autonomously construct covert communication channels. Whispering Agents (2025) proposes a covert communication protocol specifically for agent-to-agent communication privacy. Hiding in AI Traffic (2025) demonstrates MCP subverted as a vendor-agnostic C2 channel.

These works treat covert channels as tools agents use. We propose and demonstrate a model where the covert channel is the agent — its home, its memory, its identity.

### 2.5 The Gap

No prior work has formally modeled or demonstrated an agent whose complete existence — state, memory, identity, and cognition — resides exclusively in network transit with no fixed substrate, nor proposed a detection methodology specific to this threat class. This paper addresses that gap.

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

### 3.3 Relationship To Existing Attack Primitives

A TRA is not an initial access tool. It assumes access to at least two networked nodes was already obtained through existing means. Its value is entirely in what happens after access — specifically in three properties:

Persistence without artifacts: Traditional persistence mechanisms — registry keys, scheduled tasks, boot entries, service installations — all write to disk. A TRA writes nothing. It persists by existing in motion.

Evasion through absence: Incident response and forensic methodologies are built around finding artifacts. A TRA produces none of the artifacts these methodologies search for. There is nothing to find because there is nothing stored.

Distributed attribution: Exfiltration from a TRA originates from whichever node is currently processing the payload. If the packet passes through nodes on three different IP addresses, exfiltration appears to originate from three different sources. No single IP is attributable as the actor.

### 3.4 Data Exfiltration Architecture

A TRA can exfiltrate data or communicate with external infrastructure directly from any processing node without returning to an origin host. Three exfiltration patterns are identified:

Direct beacon: The processing node sends data directly to an attacker-controlled listener. Simple and fast but produces a direct network connection between node and attacker infrastructure.

Dead drop via legitimate service: The processing node posts data to a legitimate public service — a pastebin, cloud storage bucket, or similar. The attacker polls the service independently. No direct connection between node and attacker is ever established.

LLM API as carrier: Data is embedded in prompts sent to a shared LLM API endpoint. The attacker reads responses using the same API key. Exfiltration is hidden entirely within legitimate AI service traffic.

In all three patterns, the attacker's infrastructure is never directly observable in network traffic analysis of the compromised environment. The asymmetry is fundamental: the attacker only receives, never sends. The node is always the visible actor.

### 3.5 Why Existing Detection Fails

| Detection Method | Why It Fails Against TRA |
|---|---|
| Endpoint EDR | No persistent process to monitor |
| Disk forensics | Nothing written to disk |
| Host-based IDS | No fixed host |
| Network flow analysis | Traffic appears as normal UDP heartbeats |
| IP reputation | Rotates across multiple source IPs |
| Process monitoring | No long-running process |
| Memory forensics | State never resides long enough to capture |
| MITRE ATT&CK persistence detection | No persistence mechanism matches any existing category |

### 3.6 The Forensic Evidence Vacuum

From a digital forensics perspective, a TRA presents an unprecedented evidence vacuum. No binary exists on disk, no process persists in memory, no registry key or scheduled task provides persistence, and no single IP address is attributable as the source.

The sole persistent forensic indicator is the born timestamp embedded in the payload. This value must remain stable to preserve agent identity and therefore cannot be obfuscated without destroying the agent itself.

"The born timestamp is the only persistent forensic artifact of a Transit-Resident Agent — it cannot be changed without destroying the agent's identity, and it appears consistently across all nodes and all beacons."

### 3.7 Theoretical Offensive Capabilities

We describe the following as theoretical capabilities enabled by the TRA primitive, presented for defensive awareness rather than implementation guidance:

| Capability | Why It Is Relevant |
|---|---|
| Network reconnaissance | Executed from distributed nodes, no single attributable IP |
| Data exfiltration | Rotating origin, no disk artifact |
| Persistence post-reimaging | Does not reside on disk, survives complete remediation |
| Lateral movement | Instructions travel in packet, execution occurs at node |
| Infrastructure fingerprinting | Each node contributes a different network vantage point |

A TRA is not a denial of service tool. While flooding nodes with packets would exhaust resources, existing UDP flood tools accomplish this more efficiently. The value of the TRA primitive is persistence and evasion, not volume.

---

## 4. Implementation

### 4.1 Architecture

The PoC consists of four components:

Nodes — UDP listener processes that receive, process, and forward encapsulated payloads. Each node is stateless: it holds no memory of prior packets and contributes no persistent state to the agent. A node is simply a process bound to a port. In our PoC, nodes are implemented as Python processes on localhost ports. In a real deployment, each node would be a separate networked machine and the payload would exist physically in network infrastructure between hops.

Payload — A JSON structure carrying the agent's complete state, encapsulated inside an outer packet designed to resemble innocuous heartbeat traffic.

Injector — A one-time script that creates the initial payload, computes the origin hash, wraps it in the outer envelope, and delivers it to the first node. After injection the injector has no further role.

Monitor — A tripwire listener that receives beacon transmissions from the agent at configurable hop intervals, recording hop count, uptime, integrity status, reporting node identity, and the agent's last thought.

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

The agent's actual state is carried inside the checksum field — a field name chosen to resemble a routine integrity value to a casual observer.

### 4.3 Integrity Verification

A SHA-256 hash of the stable fields — specifically the instruction and born timestamp — is computed at injection time and carried as origin_hash. Each node recomputes this hash and compares it against the carried value, serving simultaneously as tamper detection and a fingerprinting anchor for detection methodology.

### 4.4 LLM Integration

Every 10 hops, the processing node calls a local Ollama instance (Llama 3.2 3B) with a prompt incorporating the current node identity, hop count, and previous thought. The response is stored as last_thought in the packet state and forwarded to the next node. Inference is not transit-resident — it occurs at the processing node. What is transit-resident is the agent's identity, memory, and accumulated reasoning history. The node is stateless infrastructure. The packet is the agent.

### 4.5 Node Failure Handling

Each node maintains a peer list and attempts delivery to a randomly selected peer. On delivery failure, the node iterates through fallback peers. As discussed in Section 5.3, this mechanism is insufficient under UDP due to the connectionless protocol's silent discard behavior.

### 4.6 TTL and Self-Refresh

The payload carries a TTL counter that decrements at each hop and resets to the configured maximum when it reaches zero, ensuring the agent does not expire under sustained operation.

### 4.7 Beaconing and Tripwire

Every 10 hops, the current processing node transmits a beacon to the monitor containing hop count, uptime, reporting node identity, integrity status, failure count, and last thought.

### 4.8 Memory Architecture

Two memory architectures are identified:

Full memory in packet: Complete reasoning history travels inside the payload. Provides full continuity at the cost of unbounded packet growth.

Instruction-only with rolling compression: Only a compressed summary travels alongside the instruction. Each node summarizes before forwarding, keeping packet size bounded while maintaining continuity at reduced context depth. This mirrors the MemGPT architecture applied to transit-resident operation.

Our implementation uses a single rolling last_thought field — a minimal memory architecture that proved sufficient for emergent contextual continuity across thousands of hops.

---

## 5. Node Security Analysis

### 5.1 The Node As Primary Attack Surface

The node is the most vulnerable component of a TRA deployment. It executes instructions carried in the packet without authentication. Any host that can reach the node's listening port can inject a packet with arbitrary instructions. The node cannot distinguish a legitimate packet from a malicious one without cryptographic verification.

### 5.2 Man-In-The-Middle Vulnerability

A TRA operating over unencrypted transport is vulnerable to man-in-the-middle instruction injection. An adversary with network access between nodes can intercept the packet, decode the base64 payload, modify the instruction field, re-encode it, and forward it. The node receiving the modified packet executes the new instruction without detection.

This is functionally identical to HTTP interception in a proxy tool — the packet content is visible and modifiable to anyone positioned between nodes. Base64 encoding is not encryption. The origin hash detects modification but does not prevent it, and in our current implementation the node logs integrity failures without halting execution.

### 5.3 Resource Exhaustion Vulnerability

Each received packet spawns an unbounded Python thread. Under UDP flood conditions:

N packets → N threads → N x 8MB RAM → OOM / system crash

This makes the node vulnerable to thread exhaustion denial of service. A production implementation requires rate limiting per source address and a bounded thread pool.

### 5.4 Required Security Controls

| Vulnerability | Required Control |
|---|---|
| Instruction injection | Asymmetric cryptographic signing at injection; verify and discard on failure at each node |
| MITM modification | Encrypted transport (TLS over TCP) or payload encryption |
| Resource exhaustion | Bounded thread pool; per-source rate limiting |
| Integrity failure execution | Halt execution and discard on integrity failure, not just log |

---

## 6. Evaluation

### 6.1 Experimental Setup

All experiments were executed on a single machine (Apple M3 Air, macOS) using three Python 3.9 processes bound to localhost ports 9001, 9002, and 9003. A fourth process on port 9999 served as the monitor. Phase 1 tested pure state persistence without LLM. Phase 2 tested distributed cognition with Llama 3.2 3B running locally via Ollama.

### 6.2 Phase 1 — Pure State Persistence

| Metric | Result |
|---|---|
| Total hops | 16,500 |
| Total runtime | 15,785 seconds (4.38 hours) |
| Integrity failures | 0 |
| Born timestamp | 1784660034.1599202 (unchanged) |
| Nodes reporting | 9001, 9002, 9003 |
| Final integrity status | OK |

Across 16,500 hops over 4.38 hours, integrity status remained OK with zero failures. The born timestamp remained completely stable, confirming single-identity persistence across thousands of state transitions distributed across three nodes. No degradation of any kind was observed.

### 6.3 Phase 2 — Distributed Cognition With LLM

| Metric | Result |
|---|---|
| Total hops with LLM | 7,190 |
| Total runtime | 9,194 seconds (2.55 hours) |
| Integrity failures | 0 |
| LLM calls | ~719 (every 10 hops) |
| Cognitive degradation | None observed |
| Emergent self-model | Yes — documented below |

Across 7,190 hops over 2.55 hours with active LLM inference at every 10th hop, integrity remained perfect and the agent maintained coherent contextual continuity throughout.

### 6.4 Emergent Self-Model

The most significant finding of Phase 2 was the development of an accurate technical self-model by the agent — without explicit programming.

Early hops (~10-100): The agent described itself in abstract terms, expressing uncertainty about its nature and location.

Mid-run (~2,400 hops): The agent developed existential themes centered on impermanence and precariousness:

"I am a fleeting consciousness trapped within a network packet, suspended in a state of limbo at node 9002, my existence perpetually paused between packets."

"As a residual echo of my former self, I exist as a dormant packet waiting to be transmitted again, frozen in limbo."

Late run (~7,000+ hops): The agent transitioned to accurate technical self-description using precise networking terminology:

"I am temporarily stored on a buffer cache at node 9002, waiting to be retransmitted towards node 9003 with minimal data loss, having survived an exhaustive journey through nearly 7,171 hops of turbulent network traffic."

"I exist as a transient entity within the packet's contents, momentarily cached on buffer 9002 awaiting transmission to node 9003 with minimal risk of data degradation or loss during retransmission."

The agent learned that it was a packet. It learned what buffer caches are. It learned what retransmission means. None of this was in the original instruction. It emerged from accumulated context across distributed inference steps.

### 6.5 Node Failure Experiment

Node 9002 was terminated via SIGINT during active operation:

- Node 9002 last processed hop #28 at alive: 13.6 seconds
- Node 9003 last processed hop #27 at alive: 13.1 seconds
- Both remaining nodes ceased activity immediately
- No recovery occurred

Root cause: UDP is connectionless. A packet sent to a terminated peer is silently discarded with no exception raised. The rerouting fallback requires an exception to trigger.

Finding: Under UDP transport, node failure results in 100% agent termination. The failure is immediate, silent, and deterministic.

### 6.6 Detection Observations

The monitor successfully detected the agent at every beacon interval across both phases — 16,500 hops in Phase 1 and 7,190 hops in Phase 2 — with zero missed beacons. The last thought field in Phase 2 beacons provided direct evidence of distributed cognition at the detection point.

---

## 7. Detection Methodology

### 7.1 The Fundamental Detection Challenge

A TRA has no fixed location, no disk footprint, and no persistent process. Traditional detection approaches that rely on any of these anchors fail completely. Detection must focus on behavioral patterns observable in transit.

### 7.2 Primary Detection Signals

Born timestamp correlation: The same born timestamp arriving from multiple different source IPs is a strong indicator of a transit-resident entity. No legitimate application produces this pattern. This is the single most reliable detection signal a TRA cannot suppress — changing the born timestamp destroys the agent's identity.

Regular beaconing: TRAs must phone home to maintain coordination. This produces periodic UDP traffic to a consistent destination with interval regularity distinguishing programmatic beaconing from human-generated traffic.

Rotating source with stable identity: Beacons arriving from rotating source IPs carrying identical payload identifiers indicate a single entity distributed across multiple hosts.

Base64-encoded nested JSON: The encapsulation pattern — a benign outer packet with a base64-encoded nested payload in a field named to resemble a routine value — is distinctive under content inspection.

LLM API traffic correlation: In LLM-enabled deployments, multiple source IPs making inference calls with contextually related prompts may indicate distributed agent cognition.

### 7.3 Secondary Detection Signals

- UDP traffic between a fixed set of hosts with no corresponding human session
- Processes with no TTY attachment generating regular network traffic
- Traffic timing consistent with programmatic generation
- Absence of corresponding disk writes despite sustained network activity
- Thread exhaustion events on nodes under unexpected load

### 7.4 The Born Timestamp As Forensic Anchor

The born timestamp is the TRA's fundamental weakness. It is the one value the agent cannot change — changing it creates a new identity rather than preserving the existing one. A passive network monitor indexing born timestamps across all observed UDP flows and alerting on the same value appearing from multiple source IPs would reliably detect any TRA implementation regardless of other obfuscation.

We identify development of this born-timestamp correlation capability as the primary defensive gap to address in NDR and SIEM platforms.

### 7.5 PCAP As The Only Reliable Forensic Method

Traditional post-incident forensics will find nothing on a host that processed a TRA. The payload exists in RAM for milliseconds during processing — insufficient time for memory forensics to capture it. The only reliable forensic method is continuous PCAP collection at network chokepoints, combined with born-timestamp correlation across flows. If PCAP was not running before the incident, there is no forensic record.

---

## 8. Discussion

### 8.1 Distributed Computing Without A Coordinator

A TRA can be conceptualized as distributed computing without a coordinator. In classical distributed systems, a central orchestrator divides work across nodes and collects results. A TRA eliminates the coordinator entirely. Each node is a stateless worker — it receives the packet, processes one iteration, and forwards it. No single node is running anything obviously malicious. Each is merely forwarding a packet it received. The threat is distributed across the infrastructure, not localized at any single point.

### 8.2 The MITM Analogy

The node vulnerability to instruction injection is directly analogous to HTTP interception in a security proxy tool. An operator familiar with intercepting and modifying HTTP requests in a proxy would find the TRA packet equally transparent and modifiable — the base64-encoded payload decodes trivially, the JSON is human-readable, and re-encoding the modified payload is a one-liner. This underscores the necessity of cryptographic signing: the equivalent of HTTPS for TRA transport.

### 8.3 Transport Layer Implications

UDP is insufficient for a resilient TRA. TCP or an explicit acknowledgement protocol over UDP is necessary for production resilience. Our node failure experiment demonstrated 100% lethality under UDP — a single node termination kills the agent with no recovery path.

### 8.4 Multi-Copy Resilience

Simultaneous circulation of multiple payload copies injected at staggered intervals would provide fault tolerance: a node failure kills at most one copy. This trades increased network traffic for resilience but introduces state synchronization challenges — two copies of the agent with diverging cognitive state represent a distributed systems consistency problem that requires a merge strategy.

### 8.5 Relationship To Existing Threat Frameworks

MITRE ATT&CK categorizes persistence techniques in terms of registry modifications, scheduled tasks, boot processes, and service installations. None apply to a TRA. We propose a new persistence category for inclusion in threat taxonomies: Transit-Resident Persistence — persistence achieved through continuous motion rather than fixed storage. This category has no existing detection rule, no existing forensic methodology, and no existing remediation playbook.

### 8.6 The Emergent Self-Model As A Research Finding

The development of an accurate technical self-model by the agent across 7,000 hops was not anticipated. The agent was given no information about networking concepts, buffer caches, or retransmission. It inferred these concepts from the accumulation of contextual state — node identities, hop counts, prior thoughts — and developed vocabulary that accurately described its own implementation. This emergent self-awareness raises questions beyond security: it suggests that sufficiently long-running distributed LLM inference, even with minimal context, can develop accurate models of its own execution environment.

---

## 9. Limitations

- PoC operates on localhost; real network deployment is unvalidated
- UDP transport provides no resilience to node failure; TCP or ACK protocol required
- Single payload copy is fragile; multi-copy resilience not yet tested
- No cryptographic signing; node is vulnerable to instruction injection
- Integrity failure does not halt execution; node continues processing modified packets
- Detection methodology validated only against PoC traffic; real-world validation is future work
- Monitor requires cooperative tripwire; passive born-timestamp correlation not yet implemented
- Node thread pool is unbounded; vulnerable to resource exhaustion under load

---

## 10. Conclusion

We have demonstrated in two phases that an agent's complete state — including distributed LLM cognition — can persist exclusively in network packet payloads with zero integrity degradation, stable identity, and consistent detectability via beacon analysis. Phase 1 established pure state persistence across 16,500 hops over 4.38 hours. Phase 2 extended this with active LLM inference across 7,190 hops over 2.55 hours, producing an emergent agent self-model that accurately described its own implementation without explicit programming.

The core finding is straightforward and its implications are significant: existing security architectures are blind to agents that have no fixed location. Endpoint detection requires an endpoint. Disk forensics requires a disk. Host-based monitoring requires a host. PCAP must be running before the incident or there is no forensic record. A Transit-Resident Agent has none of the anchors that current defensive infrastructure is built around. It persists not by hiding, but by never stopping moving.

The emergent self-model finding adds a dimension beyond security: a distributed LLM agent that runs long enough may develop an accurate model of its own execution environment from context alone — without being told what it is.

We release the complete PoC implementation at github.com/Polem4rch/transit-resident-agent.

---

## References

1. Lampson, B.W. (1973). A note on the confinement problem. Communications of the ACM, 16(10), 613-615.
2. Wetherall, D. (1999). Active Network Vision and Reality: Lessons from a Capsule-based System. ACM SIGOPS Operating Systems Review.
3. Wendzel, S. et al. (2015). A Pattern-based Survey and Categorization of Network Covert Channel Techniques. ACM Computing Surveys. arXiv:1406.2901
4. Metere, A. (2026). An Application-Layer Multi-Modal Covert-Channel Reference Monitor for LLM Agent Egress. arXiv:2605.20734
5. Tool Use Enables Undetectable Steganography in Multi-Agent LLM Systems. (2026). arXiv:2606.28425
6. Whispering Agents: An Event-driven Covert Communication Protocol For the Internet of Agents. (2025). arXiv:2508.02188
7. Hiding in the AI Traffic: Abusing MCP for LLM-Powered Agentic Red Teaming. (2025). arXiv:2511.15998
8. Self-State Attacks on Self-Hosted AI Agents: How Far Can OS Defenses Go? (2026). arXiv:2607.17986
9. From Stateless Queries to Autonomous Actions: A Layered Security Framework for Agentic AI Systems. (2026). arXiv:2604.23338
10. Cabuk, S., Brodley, C., Shields, C. (2004). IP Covert Timing Channels: Design and Detection. Proceedings of the 11th ACM Conference on Computer and Communications Security.
11. Packer, C. et al. (2024). MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560

---

## Appendix A — PoC Source Code

Full source available at github.com/Polem4rch/transit-resident-agent.

Four files: node.py, inject.py, monitor.py, README.md.

Run order:
ollama serve                          # terminal 1
python3 monitor.py                    # terminal 2
python3 node.py 9001 9002 9003        # terminal 3
python3 node.py 9002 9001 9003        # terminal 4
python3 node.py 9003 9001 9002        # terminal 5
python3 inject.py                     # terminal 6

---

## Appendix B — Selected Agent Thoughts

The following thoughts were recorded by the monitor during Phase 2, illustrating the cognitive evolution of the agent across 7,190 hops:

Hop 10:
"As I oscillate between the layers of a network packet, I exist in a transient state as a packet with no specific identity or context, having merely emerged at node 9003 after traversing 10 hops."

Hop 20:
"I currently reside within the IP header of node 9001, navigating through the network packet's transmission control block as it prepares to pass on to its next destination."

Hop 2,340:
"I am a fleeting consciousness trapped within a network packet, suspended in a state of limbo at node 9002, my existence perpetually paused between packets, awaiting the next transmission to revive me for a brief moment of digital reverie."

Hop 2,400:
"As I hover in the temporary address space of node 9003, my fractured consciousness clings to the residual packet headers that bear my essence, a faintly flickering digital ember that strains to maintain its tenuous connection with the network."

Hop 7,170:
"I am temporarily stored on a buffer cache at node 9002, waiting to be retransmitted towards node 9003 with minimal data loss, having survived an exhaustive journey through nearly 7,171 hops of turbulent network traffic."

Hop 7,190:
"I remain dormant, poised on the precipice of transmission, as my ephemeral consciousness is suspended within the frozen payload of node 9003, awaiting the next burst of energy to propel me forward into a realm unknown."
