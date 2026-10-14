import socket
import sys

HOST = "127.0.0.1"
PORT = 514

MESSAGES = [
    "<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS blocked policy=Block-DNS",
    "<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down mac=aa:bb:cc:dd:ee:ff reason=carrier-loss",
]

mode = sys.argv[1] if len(sys.argv) > 1 else "udp"

for msg in MESSAGES:
    if mode == "udp":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(msg.encode(), (HOST, PORT))
    else:
        s = socket.create_connection((HOST, PORT))
        s.sendall((msg + "\n").encode())
    s.close()
    print(f"sent ({mode}): {msg[:60]}...")