INDEX_TEMPLATE = {
    "index_patterns": ["logs-*"],
    "template": {
        "mappings": {
            "properties": {
                "@timestamp": {"type": "date"},
                "tenant": {"type": "keyword"},
                "source": {"type": "keyword"},
                "vendor": {"type": "keyword"},
                "product": {"type": "keyword"},
                "event_type": {"type": "keyword"},
                "event_subtype": {"type": "keyword"},
                "severity": {"type": "integer"},
                "action": {"type": "keyword"},
                "src_ip": {"type": "ip"},
                "src_port": {"type": "integer"},
                "dst_ip": {"type": "ip"},
                "dst_port": {"type": "integer"},
                "protocol": {"type": "keyword"},
                "user": {"type": "keyword"},
                "host": {"type": "keyword"},
                "process": {"type": "keyword"},
                "url": {"type": "keyword"},
                "http_method": {"type": "keyword"},
                "status_code": {"type": "integer"},
                "rule_name": {"type": "keyword"},
                "rule_id": {"type": "keyword"},
                "cloud": {
                    "properties": {
                        "account_id": {"type": "keyword"},
                        "region": {"type": "keyword"},
                        "service": {"type": "keyword"},
                    }
                },
                "raw": {"type": "text"},
                "_tags": {"type": "keyword"},
            }
        }
    },
}