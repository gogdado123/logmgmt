# Setup: Appliance (เครื่อง/VM เดียว)

## ข้อกำหนดขั้นต่ำ

- Ubuntu 22.04+ (ทดสอบบน 24.04), 4 vCPU, 8 GB RAM (ขั้นต่ำที่ทดสอบได้จริงคือ ~4 GB), ดิสก์ 40 GB
- พอร์ตที่ต้องเปิด: **80, 443** (เว็บ), **514 TCP/UDP** (Syslog)
- ไม่ต้องเปิด 9200 (OpenSearch) และ 8000 (backend)

## 1. ติดตั้ง Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# ออกจากระบบแล้วเข้าใหม่ เพื่อให้สิทธิ์กลุ่ม docker มีผล
docker --version && docker compose version
```

## 2. ตั้งค่าเคอร์เนลสำหรับ OpenSearch

```bash
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-opensearch.conf
```

เครื่อง RAM 4 GB แนะนำเพิ่ม swap:

```bash
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
```

## 3. ดึงโค้ด

```bash
git clone https://github.com/gogdado123/logmgmt.git logmgmt
cd logmgmt
```

## 4. ตั้งค่า `.env`

```bash
JWT=$(openssl rand -hex 32)
KEY=$(openssl rand -hex 24)
cat > .env <<EOF
OPENSEARCH_URL=http://opensearch:9200
JWT_SECRET=$JWT
INGEST_API_KEY=$KEY
ALERT_THRESHOLD=5
ALERT_WINDOW_MIN=5
ALERT_WEBHOOK_URL=
RETENTION_DAYS=7
SITE_ADDRESS=localhost
SYSLOG_TENANT=demoa
EOF
echo "INGEST_API_KEY = $KEY"    # จดไว้ใช้ส่ง log
```

| ตัวแปร | ความหมาย |
|---|---|
| `JWT_SECRET` | คีย์เซ็น JWT (สุ่มใหม่ทุกเครื่อง) |
| `INGEST_API_KEY` | คีย์สำหรับ `/ingest` และ Syslog listener |
| `SITE_ADDRESS` | `localhost` หรือ IP/ชื่อโดเมนของเครื่อง (ดูหมายเหตุด้านล่าง) |
| `SYSLOG_TENANT` | tenant ของ log ที่เข้าทาง Syslog |
| `ALERT_WEBHOOK_URL` | ว่างได้ ถ้าใส่ระบบจะ POST JSON ของ alert ไปที่ URL นี้ |
| `ALERT_THRESHOLD` / `ALERT_WINDOW_MIN` | เงื่อนไข alert (จำนวนครั้ง / นาที) |
| `RETENTION_DAYS` | จำนวนวันที่เก็บ log |

### หมายเหตุเรื่อง `SITE_ADDRESS`

`SITE_ADDRESS` คือชื่อเดียวที่ Caddy ยอมรับ ต้องเปิดเว็บและเรียก API ด้วยชื่อนี้เสมอ

- **`localhost`** (ค่าเริ่มต้น): เปิด `https://localhost` ได้เฉพาะบนเครื่องที่รันระบบ
  หากต้องการเปิดเบราว์เซอร์จากเครื่องอื่น ให้ทำ SSH Tunnel โดยรันคำสั่งนี้ **บนเครื่องที่จะเปิดเบราว์เซอร์** (ไม่ใช่บน VM) แล้วเปิดหน้าต่างนั้นค้างไว้:

  ```bash
  ssh -L 8443:localhost:443 <user>@<IP_VM>
  ```

  จากนั้นเปิด `https://localhost:8443`
- **IP ของเครื่อง** (เช่น `192.168.1.50`): ต้องเปิดและเรียก API ผ่าน `https://192.168.1.50` เท่านั้น
- การเรียกด้วยชื่ออื่นที่ไม่ตรงกับ `SITE_ADDRESS` จะได้ `tlsv1 alert internal error`

## 5. สร้างผู้ใช้

```bash
mkdir -p data
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml run --rm \
  -e ADMIN_PASSWORD='ตั้งรหัสแอดมิน' -e VIEWER_PASSWORD='ตั้งรหัสviewer' \
  -v "$PWD/data:/data" -w /data backend python /app/make_users.py
ls data      # ต้องเห็น users.json
```

ได้ผู้ใช้ `admin` (ทุก tenant), `viewerA` (tenant `demoa`), `viewerB` (tenant `demob`)

## 6. เริ่มระบบ

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps     # ต้องเห็น 4 service Up
```

หรือ `make up` ครั้งแรกใช้เวลาหลายนาทีเพราะต้อง build และโหลด image OpenSearch

## 7. ตรวจสอบ

```bash
curl -k https://localhost/api/health      # {"status":"ok"}  (กรณี SITE_ADDRESS=localhost)
curl localhost:9200                       # ต้อง connection refused (ตั้งใจปิด)
```

ถ้าตั้ง `SITE_ADDRESS` เป็น IP ให้เปลี่ยน `localhost` ในคำสั่งแรกเป็น IP นั้น

เปิดเบราว์เซอร์ที่ `https://localhost` (หรือ `https://localhost:8443` หากทำ SSH Tunnel หรือ `https://<IP เครื่อง>` ตาม `SITE_ADDRESS`)

### เรื่องใบรับรอง (self-signed)

โหมด Appliance ไม่มีโดเมนสาธารณะ Caddy จึงออกใบรับรองจาก CA ภายในของตัวเอง เบราว์เซอร์จะขึ้น "Not secure" ให้กด **Advanced → Proceed** การเชื่อมต่อยังถูกเข้ารหัสด้วย TLS ตามปกติ ถ้าต้องการให้เบราว์เซอร์เชื่อถือ ให้นำใบรับรอง root ของ Caddy ไป trust:

```bash
docker compose -f docker-compose.prod.yml cp caddy:/data/caddy/pki/authorities/local/root.crt ./caddy-root.crt
```

## 8. ทดสอบ Acceptance

> **ใบรับรอง self-signed:** `curl` ใช้ `-k` เพื่อข้ามการตรวจใบรับรอง ส่วนสคริปต์ Python (`samples/seed_now.py`)
> ให้ใส่ `INSECURE=1` นำหน้าคำสั่งเพื่อข้ามการตรวจเช่นกัน
> `tests/test_tenant_isolation.py` ก็เจอปัญหาเดียวกันหากชี้ไปที่ Appliance (แนะนำให้รันกับโหมด SaaS ที่มีใบรับรองจริง)

```bash
export INGEST_URL=https://localhost/api/ingest     # ถ้า SITE_ADDRESS เป็น IP ให้ใช้ IP แทน localhost
export INGEST_API_KEY=<key ที่จดไว้>

# 1) Syslog → เห็นใน UI ภายใน 1 นาที (ส่งจากเครื่องเดียวกัน; จากเครื่องอื่นตั้ง SYSLOG_HOST=<IP เครื่องนี้>)
python3 samples/send_syslog.py udp
python3 samples/send_syslog.py tcp

# 2) HTTP JSON แล้วค้นหา
curl -k -X POST https://localhost/api/ingest -H "X-API-Key: $INGEST_API_KEY" \
  -H "Content-Type: application/json" -d @samples/api_login_failed.json

# 3) ไฟล์ batch AWS / M365 / AD
curl -k -X POST https://localhost/api/ingest/file -H "X-API-Key: $INGEST_API_KEY" \
  -F "file=@samples/batch_aws_m365_ad.json"

# 4) ข้อมูลเวลาปัจจุบัน + ชุด login ล้มเหลว เพื่อให้ Alert ทำงาน
INSECURE=1 python3 samples/seed_now.py
```

> ข้อมูลตัวอย่างที่ timestamp เก่ากว่า 7 วัน (เช่น `api_login_failed.json`, `batch_aws_m365_ad.json`) จะถูกลบโดย Retention ภายในชั่วโมงถัดไป
> และจะไม่ปรากฏใน Dashboard ช่วง 24 ชั่วโมง ใช้ `seed_now.py` สำหรับเดโม

จากนั้นใน UI:

1. ล็อกอิน `admin` → Dashboard เห็น Timeline / Top N → แท็บ **Alerts** เห็น `repeated-login-failure` (รอ ≤ 30 วินาที หรือ `POST /admin/alerts/check`)
2. ล็อกอิน `viewerA` → เห็นเฉพาะ tenant `demoa`; ขอ `tenant=demoB` ได้ `403`
3. Retention: ส่ง event ที่ timestamp เก่า แล้วเรียก `POST /admin/retention/run` (ต้องใช้ token admin)

## การดูแล

```bash
docker compose -f docker-compose.prod.yml logs -f --tail=100 backend
docker compose -f docker-compose.prod.yml down          # หยุด (ข้อมูลยังอยู่ใน volume)
docker compose -f docker-compose.prod.yml down -v       # หยุดและลบข้อมูลทั้งหมด
```

## ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| OpenSearch ออกจากการทำงานทันที | `vm.max_map_count` ต่ำ หรือ RAM ไม่พอ (ลด heap ใน compose เป็น `-Xms512m -Xmx512m`) |
| `port is already allocated` | มี service อื่นใช้ 80/443/514 อยู่ หรือยังไม่ได้หยุดชุดพัฒนา (`docker compose down`) |
| เว็บขึ้น 502/500 ช่วงแรก | OpenSearch ยังเริ่มไม่เสร็จ รอ 1–2 นาที (service มี `restart: unless-stopped`) |
| `tlsv1 alert internal error` | เรียก URL ไม่ตรงกับชื่อที่ตั้งไว้ใน `SITE_ADDRESS` (เช่น ตั้งเป็น IP แต่เรียกผ่าน `localhost`) |
| `CERTIFICATE_VERIFY_FAILED` ในสคริปต์ Python | Appliance ใช้ใบรับรอง self-signed ให้ใส่ `INSECURE=1` นำหน้าคำสั่ง |
| `localhost refused to connect` ตอนใช้ SSH Tunnel | รัน `ssh -L` บน VM แทนที่จะรันบนเครื่องที่เปิดเบราว์เซอร์ ให้ออกจาก VM แล้วรันใหม่จากเครื่องของตัวเอง |
| login แล้วเด้งออก | เปลี่ยน `JWT_SECRET` แล้ว token เก่าใช้ไม่ได้ ให้ login ใหม่ |
