# Backend - Hệ Thống Quản Lý Tồn Kho Căng Tin CTECH

FastAPI + SQLite + SQLAlchemy + JWT

## Khởi chạy Backend

1. Cài đặt thư viện:
```bash
pip install -r requirements.txt
```

2. Khởi tạo dữ liệu mẫu (20 SKU, 30 ngày lịch sử, tài khoản):
```bash
python seed_data.py
```

3. Chạy API Server:
```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Tài khoản mẫu:
- **Quản lý:** `admin` / `admin123`
- **Nhân viên:** `nhanvien` / `nv123`
