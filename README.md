# Log Management Demo

ระบบ Log Management แบบ mini-SIEM รับ log หลายแหล่ง แปลงเป็น Schema กลาง เก็บแบบค้นหาได้ แสดง Dashboard และแจ้งเตือน รองรับ multi-tenant และติดตั้งได้ 2 โหมด (Appliance / SaaS)

ผู้พัฒนา: 'นายอมริน ศรีพงษ์'

## Tech Stack

| ส่วน | เทคโนโลยี |
|---|---|
| Ingest | FastAPI `POST /ingest`, `POST /ingest/file`, Python Syslog listener (UDP+TCP 514) |
| Normalize | Parser แยกต่อ source ใน `backend/parsers/` |
| Storage | OpenSearch 2.15 (index แยกต่อ tenant ต่อวัน) |
| Backend | FastAPI + JWT (PyJWT) + bcrypt |
| Frontend | React (Vite) + Recharts |
| Reverse proxy / TLS | Caddy (HTTPS อัตโนมัติ) |
| Deploy | Docker Compose (ไฟล์เดียวใช้ได้ทั้ง Appliance และ SaaS) |

## ลิงก์สำหรับกรรมการ

- SaaS: `https://gogdado-logmgmt.duckdns.org`
- บัญชีทดสอบ (ส่งรหัสผ่านแยกทางอีเมล)

| Username | Role | Tenant ที่เข้าถึงได้ | Password |
|---|---|---|---|
| `admin` | admin | ทุก tenant | `r3L9t@Z,+6.6` |
| `viewerA` | viewer | `demoa` | "T89c8k`Z2jQs" |
| `viewerB` | viewer | `demob` | "T89c8k`Z2jQs" |

- `INGEST_API_KEY` สำหรับส่ง log เข้า SaaS: `066ebd355a70e183f458e7fecf4fd7977f0fc2af11416ef0`

## Quick Start (Appliance, เครื่องเดียว)

ดูรายละเอียดใน [docs/setup_appliance.md](docs/setup_appliance.md) แบบย่อ:

```bash
git clone https://github.com/gogdado123/logmgmt.git logmgmt && cd logmgmt
cp .env.example .env            # แก้ JWT_SECRET และ INGEST_API_KEY
mkdir -p data
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml run --rm \
  -e ADMIN_PASSWORD='ตั้งเอง' -e VIEWER_PASSWORD='ตั้งเอง' \
  -v "$PWD/data:/data" -w /data backend python /app/make_users.py
docker compose -f docker-compose.prod.yml up -d --build
```

เปิด `https://localhost` (ใบรับรอง self-signed ให้กด Advanced > Proceed)

## ส่ง log ทดสอบ

```bash
# สร้างข้อมูลเวลาปัจจุบัน (มีชุด login ล้มเหลวซ้ำเพื่อทดสอบ Alert)
export INGEST_URL=https://localhost/api/ingest INGEST_API_KEY=<key>
python samples/seed_now.py

# HTTP JSON
curl -k -X POST https://localhost/api/ingest -H "X-API-Key: <key>" \
  -H "Content-Type: application/json" -d @samples/api_login_failed.json

# ไฟล์ batch (AWS / M365 / AD)
curl -k -X POST https://localhost/api/ingest/file -H "X-API-Key: <key>" \
  -F "file=@samples/batch_aws_m365_ad.json"

# Syslog (UDP หรือ TCP)
python samples/send_syslog.py udp
python samples/send_syslog.py tcp
```

> หมายเหตุ: ไฟล์ตัวอย่างใน `samples/` บางไฟล์ใช้ timestamp ปี 2025/ส.ค. ซึ่งเก่ากว่า 7 วัน job Retention จะลบทิ้งภายในชั่วโมงถัดไป สำหรับเดโมให้ใช้ `seed_now.py` (ใช้เวลาปัจจุบัน) หรือสั่งรัน Retention เองเพื่อโชว์

## คำสั่งที่ใช้บ่อย (Makefile)

| คำสั่ง | ความหมาย |
|---|---|
| `make up` | build และรันทั้งระบบ |
| `make down` | หยุดระบบ |
| `make logs` | ดู log ของทุก service |
| `make seed` | ส่งข้อมูลตัวอย่างเวลาปัจจุบัน |
| `make test` | รัน pytest |

## API หลัก

| Endpoint | สิทธิ์ | หน้าที่ |
|---|---|---|
| `POST /auth/login` | - | ล็อกอิน รับ JWT |
| `GET /me` | JWT | ข้อมูลผู้ใช้ |
| `POST /ingest` | `X-API-Key` | รับ log 1 รายการ (JSON) |
| `POST /ingest/file` | `X-API-Key` | อัปโหลดไฟล์ JSON array / NDJSON |
| `GET /search` | JWT | ค้นหา (`q`, `tenant`, `source`, `start`, `end`, `size`) |
| `GET /stats/top` | JWT | Top N ของ `src_ip/user/host/event_type/...` |
| `GET /stats/timeline` | JWT | จำนวน event ตามเวลา (`1m/5m/15m/1h/1d`) |
| `GET /alerts` | JWT | รายการแจ้งเตือน |
| `POST /admin/alerts/check` | admin | สั่งตรวจ alert ทันที |
| `POST /admin/retention/run` | admin | สั่งลบข้อมูลเกิน 7 วันทันที |

ผ่าน Caddy ทุก endpoint อยู่ใต้ prefix `/api` เช่น `/api/search`

## โครงสร้าง repo

```
backend/      FastAPI: auth, ingest, search, alerts, retention, parsers/
ingest/       Syslog listener (UDP+TCP) ส่งต่อเข้า backend
frontend/     React dashboard (Dockerfile build เป็น static ให้ Caddy)
samples/      log ตัวอย่าง + send_syslog.py + seed_now.py
tests/        pytest (parser + tenant isolation)
docs/         architecture, setup_appliance, setup_saas, schema
Caddyfile     HTTPS + proxy /api
docker-compose.prod.yml   ชุดใช้งานจริง (Appliance/SaaS)
docker-compose.yml        ชุดพัฒนา (เปิดพอร์ต 9200/8000)
```

## ทดสอบ

```bash
pip install pytest
python -m pytest tests/test_parsers.py -v          # unit
BASE_URL=https://<host>/api VIEWER_PASSWORD=<pw> python -m pytest tests -v   # รวม integration
```

## ข้อจำกัดที่ทราบ

- Syslog listener กำหนด tenant ต่อ 1 listener ผ่าน `SYSLOG_TENANT` และไม่มี authentication (เหมาะกับเดโม ควรจำกัด IP ที่ firewall)
- Syslog ไม่มีปีในข้อความ ระบบใช้ปีปัจจุบัน (UTC)
- ผู้ใช้เก็บในไฟล์ `data/users.json` (เหมาะกับเดโม ไม่ใช่ production)
- OpenSearch ปิด security plugin และไม่เปิดพอร์ตออกนอก network ของ Docker
