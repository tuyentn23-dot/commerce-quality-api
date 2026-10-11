# Commerce Data Quality API — MVP

Ba chức năng đã chạy kiểm thử local, chưa được triển khai hoặc đăng RapidAPI:

| Chức năng | Endpoint | Đầu vào / giới hạn | Kết quả |
|---|---|---|---|
| Invoice Arithmetic Validator | POST `/v1/invoices/validate` | Số tiền dạng chuỗi thập phân; tối đa 200 dòng | Sai lệch total, subtotal, từng dòng |
| VN Contact Cleaner | POST `/v1/contacts/normalize` | 1–200 contact | Email domain chuẩn hóa, phone +84, cờ kiểm tra cú pháp |
| Batch Duplicate Detector | POST `/v1/records/duplicate-candidates` | 1–500 record; 1–8 key_fields | Nhóm chỉ số trùng; bỏ qua key thiếu; không xóa dữ liệu |

Invoice chỉ kiểm tra phép tính, không xác minh hóa đơn hoặc tính đúng đắn của thuế. Contact chỉ kiểm tra cú pháp (email dùng một tập con dot-atom ASCII bảo thủ; phone kiểm tra hình dạng số di động Việt Nam), không xác minh số đang hoạt động, chủ sở hữu, email nhận được thư hoặc đầu số đang được cấp. Duplicate là exact-match theo key khách chọn, cần xem lại các nhóm trước khi xử lý. Mỗi request giới hạn 1 MB.

## Chạy

```powershell
cd D:/TNT_AI/venture_foundry/rapidapi_extract/products/commerce_quality
pip install -r requirements.txt
# Đặt RAPIDAPI_PROXY_SECRET, ADMIN_TOKEN và METRICS_HASH_SECRET trong môi trường.
uvicorn main:app --host 127.0.0.1 --port 8010
```

Không lưu secret vào file tracked. Service từ chối các đường dẫn nghiệp vụ nếu thiếu `RAPIDAPI_PROXY_SECRET`. `/health` public; `/metrics` cần `Authorization: Bearer <ADMIN_TOKEN>`. Các endpoint nghiệp vụ, `/docs`, `/openapi.json` cần `X-RapidAPI-Proxy-Secret`. File OpenAPI import được export offline, không yêu cầu công khai docs có secret.

Metrics dùng SQLite (tổng call/error theo endpoint và HMAC của RapidAPI user ID), không lưu payload hoặc user ID thô. Đặt `METRICS_HASH_SECRET` ổn định để đếm observed users; thiếu biến thì count là null, không giả số 0. Giữ secret ổn định: đổi secret sẽ tạo danh tính mới cho cùng user. Health và metrics không bị tính vào traffic. Monitoring không thể suy ra subscriber gói trả phí hay doanh thu.

Deploy dùng `Dockerfile`, root directory là `products/commerce_quality`; đặt `PORT` nếu hosting yêu cầu. SQLite cần volume bền vững: đặt `METRICS_DB=/data/usage.sqlite3` khi `/data` đã được mount. Chạy một instance cho MVP; nhiều instance cần shared database thay SQLite. Không dùng counter trên filesystem ephemeral để báo doanh thu.

## Ví dụ

Invoice:
```json
{"subtotal":"100","tax":"10","shipping":"5","discount":"0","total":"115","lines":[{"quantity":"2","unit_price":"50","line_total":"100"}]}
```

Contact:
```json
{"contacts":[{"email":"User@EXAMPLE.COM","phone":"+84 912 345 678"}]}
```

Duplicate:
```json
{"records":[{"source":"shop-a","order_id":"A1"},{"source":"shop-a","order_id":"A1"}],"key_fields":["source","order_id"]}
```

## Kiểm thử và xuất listing

```powershell
& D:/TNT_AI/venv/Scripts/python.exe products/commerce_quality/test_quality.py -v
& D:/TNT_AI/venv/Scripts/python.exe products/commerce_quality/export_openapi.py
```

`openapi.import.json` chứa cả ba endpoint; các file `openapi.invoice.json`, `openapi.contacts.json`, `openapi.duplicates.json` phục vụ thử nghiệm listing riêng trên cùng backend. Chưa đặt URL server vì chưa có deployment mới. Chỉ tạo listing được chọn sau khi có URL backend thật và proxy secret được cấu hình. Không thêm dịch vụ chưa deploy vào registry của tray.
