import os
import socketserver
import threading
import requests

BACKEND = os.environ.get("BACKEND_URL", "http://backend:8000/ingest")
TENANT = os.environ.get("SYSLOG_TENANT", "demoa")
PORT = int(os.environ.get("SYSLOG_PORT", "514"))


def classify(line: str) -> str:
    # แยก router กับ firewall จากคีย์ที่พบในข้อความ
    return "network" if " event=" in line and " action=" not in line else "firewall"


def forward(line: str):
    line = line.strip()
    if not line:
        return
    try:
        r = requests.post(
            BACKEND,
            json={"tenant": TENANT, "source": classify(line), "message": line},
            timeout=5,
        )
        if r.status_code != 200:
            print(f"backend rejected ({r.status_code}): {r.text}", flush=True)
    except requests.RequestException as e:
        print(f"forward failed: {e}", flush=True)


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].decode("utf-8", errors="replace")
        for line in data.splitlines():
            forward(line)


class TCPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        for raw in self.rfile:
            forward(raw.decode("utf-8", errors="replace"))


class ThreadedTCP(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    udp = socketserver.UDPServer(("0.0.0.0", PORT), UDPHandler)
    tcp = ThreadedTCP(("0.0.0.0", PORT), TCPHandler)
    threading.Thread(target=udp.serve_forever, daemon=True).start()
    print(f"syslog listening on {PORT} (udp+tcp), tenant={TENANT}", flush=True)
    tcp.serve_forever()