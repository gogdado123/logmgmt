import asyncio
import os
import re
from datetime import datetime, timedelta, timezone

import storage

RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "7"))
PATTERN = re.compile(r"^logs-.+-(\d{4})\.(\d{2})\.(\d{2})$")


def purge_once():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).date()
    deleted = []
    for name in storage.client.indices.get(index="logs-*").keys():
        m = PATTERN.match(name)
        if not m:
            continue
        day = datetime(int(m[1]), int(m[2]), int(m[3])).date()
        if day < cutoff:
            storage.client.indices.delete(index=name)
            deleted.append(name)
    if deleted:
        print(f"retention deleted: {deleted}", flush=True)
    return deleted


async def loop():
    while True:
        try:
            await asyncio.to_thread(purge_once)
        except Exception as e:
            print(f"retention failed: {e}", flush=True)
        await asyncio.sleep(3600)