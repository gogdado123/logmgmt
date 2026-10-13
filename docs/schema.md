# Central Schema

ทุก log จากทุกแหล่งต้องถูก normalize ให้เป็นรูปแบบนี้ก่อนเก็บลง OpenSearch

## ฟิลด์หลัก

| ฟิลด์ | ชนิด (OpenSearch) | คำอธิบาย |
|---|---|---|
| @timestamp | date | เวลาเกิดเหตุการณ์ (RFC3339) |
| tenant | keyword | ลูกค้า/องค์กรเจ้าของ log |
| source | keyword | firewall, crowdstrike, aws, m365, ad, api, network |
| vendor | keyword | ผู้ผลิต |
| product | keyword | ชื่อผลิตภัณฑ์ |
| event_type | keyword | ประเภทเหตุการณ์ |
| event_subtype | keyword | ประเภทย่อย |
| severity | integer | ความรุนแรง 0-10 |
| action | keyword | allow, deny, create, delete, login, logout, alert |
| src_ip | ip | IP ต้นทาง |
| src_port | integer | พอร์ตต้นทาง |
| dst_ip | ip | IP ปลายทาง |
| dst_port | integer | พอร์ตปลายทาง |
| protocol | keyword | tcp, udp ฯลฯ |
| user | keyword | ชื่อผู้ใช้ |
| host | keyword | ชื่อเครื่อง |
| process | keyword | ชื่อโปรเซส |
| url | keyword | URL |
| http_method | keyword | GET, POST ฯลฯ |
| status_code | integer | HTTP status code |
| rule_name | keyword | ชื่อกฎ/นโยบาย |
| rule_id | keyword | รหัสกฎ |
| cloud.account_id | keyword | AWS account |
| cloud.region | keyword | region |
| cloud.service | keyword | บริการคลาวด์ |
| raw | text | ข้อความดิบต้นฉบับ |
| _tags | keyword (array) | แท็กเพิ่มเติม |

## หลักการออกแบบ

- ฟิลด์ที่ใช้ทำ Top N ใช้ `keyword`
- IP ใช้ชนิด `ip` เพื่อค้นช่วงและ aggregate ได้
- index แยกต่อ tenant ต่อวัน ตั้งชื่อ `logs-{tenant}-{YYYY.MM.DD}` เพื่อทำ retention โดยลบ index เก่า