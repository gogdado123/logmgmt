# Setup: SaaS / Cloud (Azure VM + DuckDNS + HTTPS)

ใช้ไฟล์ `docker-compose.prod.yml` ชุดเดียวกับ Appliance ต่างกันที่ `.env` (โดเมนจริง) และมี DNS/Firewall บนคลาวด์

URL เดโม: `https://gogdado-logmgmt.duckdns.org`

## 1. สร้าง VM บน Azure

| หัวข้อ | ค่าที่ใช้ |
-----------------
| Subscription | Azure for Students |
| Region | Southeast Asia |
| Image | Ubuntu Server 24.04 LTS |
| Size | Standard B2ls_v2 (RAM ≈ 3.8 GiB ตรวจด้วย `free -h`) |
| OS disk | 64 GiB |
| Authentication | Password (username `azureuser`) |

หลังสร้างเสร็จ ตั้ง Public IP เป็น **Static** (Public IP → Configuration → Assignment: Static) เพื่อไม่ให้ IP เปลี่ยนเมื่อ Stop/Start

## 2. เปิด Firewall (Network Security Group)

| Priority | ชื่อ | พอร์ต | โปรโตคอล |
------------------------------------
| 300 | SSH | 22 | TCP (แนะนำจำกัด Source เป็น IP ผู้ดูแล) |
| 310 | allow-http-80 | 80 | TCP (Caddy ใช้พิสูจน์โดเมนกับ Let's Encrypt) |
| 320 | allow-https-443 | 443 | TCP |
| 330 | allow-syslog-514 | 514 | Any (TCP+UDP) |

**ห้ามเปิด 9200 และ 8000** เพราะ OpenSearch ไม่ได้เปิด security plugin

## 3. โดเมน (DuckDNS)

1. เข้า https://www.duckdns.org สร้าง subdomain (`gogdado-logmgmt`)
2. ใส่ Public IP ของ VM ในช่อง current ip แล้ว update
3. ตรวจ: `nslookup gogdado-logmgmt.duckdns.org` ต้องได้ IP ของ VM

เมื่อมีโดเมนจริง Caddy จะขอใบรับรองจาก Let's Encrypt ให้อัตโนมัติ เบราว์เซอร์จะไม่ขึ้นคำเตือน

## 4. เตรียมเครื่อง

```bash
ssh azureuser@<PUBLIC_IP>

# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker azureuser
exit && ssh azureuser@<PUBLIC_IP>

# เคอร์เนลสำหรับ OpenSearch + swap (RAM ~4 GB)
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-opensearch.conf
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 5. ดึงโค้ด (repo เป็น private)

สร้าง Personal Access Token (GitHub → Settings → Developer settings → Tokens, scope `repo`, อายุสั้น) แล้ว:

```bash
git clone https://github.com/gogdado123/logmgmt.git logmgmt      # username = ชื่อ GitHub, password = token
cd logmgmt
```

## 6. ตั้งค่า `.env` ด้วยรหัสลับจริง

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
SITE_ADDRESS=gogdado-logmgmt.duckdns.org
SYSLOG_TENANT=demoa
EOF
echo "INGEST_API_KEY = $KEY"
```

> ระวัง: อย่ารัน `cp .env.example .env` ทับไฟล์นี้บน VM ที่ตั้งค่าแล้ว

## 7. สร้างผู้ใช้ (รหัสผ่านจริง ไม่ใช่รหัสเดโม)

```bash
mkdir -p data
docker compose -f docker-compose.prod.yml build backend
docker compose -f docker-compose.prod.yml run --rm \
  -e ADMIN_PASSWORD='...' -e VIEWER_PASSWORD='...' \
  -v "$PWD/data:/data" -w /data backend python /app/make_users.py
```

## 8. เริ่มระบบและตรวจสอบ

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs caddy     # ดูการขอใบรับรอง
```

จากเครื่องใดก็ได้:

```bash
curl https://gogdado-logmgmt.duckdns.org/api/health      # {"status":"ok"}
```

เปิด `https://gogdado-logmgmt.duckdns.org` ต้องไม่มี "Not secure"

## 9. ส่ง log เข้า SaaS

```bash
curl -X POST https://gogdado-logmgmt.duckdns.org/api/ingest \
  -H "X-API-Key: <INGEST_API_KEY>" -H "Content-Type: application/json" \
  -d @samples/api_login_failed.json

# ข้อมูลเวลาปัจจุบัน
export INGEST_URL=https://gogdado-logmgmt.duckdns.org/api/ingest INGEST_API_KEY=<key>
python samples/seed_now.py

# Syslog (แก้ HOST ใน samples/send_syslog.py เป็นชื่อโดเมน)
python samples/send_syslog.py udp
```

## 10. ทดสอบอัตโนมัติ

```bash
BASE_URL=https://gogdado-logmgmt.duckdns.org/api VIEWER_PASSWORD=<pw viewer> python -m pytest tests -v
```

ต้องผ่าน 5 เคส (parser 3 + tenant isolation 2)

## 11. การอัปเดต

```bash
cd ~/logmgmt && git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## ความปลอดภัยและค่าใช้จ่าย

- เปลี่ยนรหัสผ่านผู้ใช้ `JWT_SECRET` และ `INGEST_API_KEY` ให้ต่างจากค่าเดโมเสมอ และสุ่มใหม่ทันทีหากค่าเคยหลุด
- จำกัด Source ของกฎ SSH และ Syslog (514) เป็น IP ที่ใช้งานจริง
- หลังจบการประเมิน ให้ลบ Resource group logmgmt-rg ทั้งก้อนเพื่อไม่ให้เสียเครดิต (หรืออย่างน้อย Stop แบบ Deallocate)