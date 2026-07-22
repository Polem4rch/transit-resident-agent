import socket
import json
import time

MONITOR_PORT = 9999

def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", MONITOR_PORT))
    print(f"[MONITOR] listening on port {MONITOR_PORT}")
    print(f"[MONITOR] waiting for agent beacon...\n")

    while True:
        data, addr = sock.recvfrom(65535)
        beacon = json.loads(data.decode())
        print("=" * 60)
        print(f"[ALERT] agent detected at {time.strftime('%H:%M:%S')}")
        print(f"[ALERT] from node:       {beacon.get('from_node')}")
        print(f"[ALERT] hops so far:     {beacon.get('hops')}")
        print(f"[ALERT] alive for:       {beacon.get('alive_seconds'):.1f}s")
        print(f"[ALERT] integrity:       {beacon.get('integrity_status')}")
        print(f"[ALERT] failures:        {beacon.get('integrity_failures')}")
        print(f"[ALERT] last thought:    {beacon.get('last_thought')}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    listen()
