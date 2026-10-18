import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from parsers import ad, firewall, network  # noqa: E402

FW = ("<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny "
      "src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS blocked policy=Block-DNS")
RTR = "<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down mac=aa:bb:cc:dd:ee:ff reason=carrier-loss"


def test_firewall_maps_fields():
    d = firewall.parse({"tenant": "demoa", "message": FW})
    assert d["source"] == "firewall"
    assert d["src_ip"] == "10.0.1.10" and d["dst_ip"] == "8.8.8.8"
    assert d["src_port"] == 5353 and d["dst_port"] == 53
    assert d["protocol"] == "udp" and d["rule_name"] == "Block-DNS"
    assert d["action"] == "deny"


def test_network_router_event():
    d = network.parse({"tenant": "demoa", "message": RTR})
    assert d["event_type"] == "link-down"
    assert d["event_subtype"] == "carrier-loss"
    assert d["host"] == "r1"


def test_ad_4625_is_failed_login():
    d = ad.parse({"tenant": "demoa", "event_id": 4625, "event_type": "LogonFailed",
                  "user": "demo\\eve", "host": "DC01", "ip": "203.0.113.77"})
    assert d["event_type"] == "LogonFailed"
    assert d["action"] == "login" and d["severity"] == 5
    assert d["src_ip"] == "203.0.113.77"