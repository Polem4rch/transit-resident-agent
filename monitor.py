import socket
import json
import time

MONITOR_PORT = 9999

def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", MONITOR_PORT))
    print(f"[MONITOR] listening on port {MONITOR_PORT}\n")

    while True:
        data, addr = sock.recvfrom(65535)
        beacon = json.loads(data.decode())
        m = beacon.get("metrics", {})
        print("=" * 60)
        print(f"[ALERT] {time.strftime('%H:%M:%S')} | node: {beacon.get('from_node')} | hops: {beacon.get('hops')}")
        print(f"[ALERT] alive: {beacon.get('alive_seconds'):.1f}s | integrity: {beacon.get('integrity_status')} | failures: {beacon.get('integrity_failures')}")
        print(f"[METRICS] packet size now: {m.get('current_packet_size_bytes')}B | avg: {m.get('avg_packet_size_bytes')}B")
        print(f"[METRICS] avg RTT: {m.get('avg_rtt_ms')}ms | bandwidth: {m.get('total_bandwidth_kb')}KB")
        print(f"[METRICS] avg CPU: {m.get('avg_cpu_percent')}% | avg RAM: {m.get('avg_ram_mb')}MB")
        print(f"[METRICS] avg LLM latency: {m.get('avg_llm_latency_s')}s")
        print(f"[THOUGHT] {beacon.get('last_thought')}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    listen()
