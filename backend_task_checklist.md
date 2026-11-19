# 🛠️ BACKEND TASK CHECKLIST – HỆ THỐNG QUẢN LÝ TỒN KHO CĂNG TIN CTECH

> **Kiến trúc:** FastAPI + SQLite + SQLAlchemy 2.0 + Pydantic v2 + python-jose (JWT) + Passlib (Bcrypt)  
> **Trạng thái tổng thể:** ✅ Đã hoàn thành 100% & Vượt qua 8/8 kịch bản kiểm thử tự động (`test_api.py`)

---

## 📋 BẢNG CHECKLIST CHI TIẾT TỪNG MODULE BACKEND

### 1. Hạ Tầng & Cấu Hình (`app/core/`)
- [x] **Cài đặt thư viện:** `fastapi`, `uvicorn`, `sqlalchemy`, `python-jose`, `passlib`, `pydantic` (`requirements.txt`)
- [x] **Cấu hình kết nối Database:** SQLite engine đa luồng (`check_same_thread=False`), SessionLocal, Base (`app/core/database.py`)
- [x] **Cấu hình Bảo mật:** `SECRET_KEY`, thuật toán `HS256`, thời hạn Token 12 giờ (`app/core/config.py`)
- [x] **Security Utility:** Băm mật khẩu (bcrypt), đối soát mật khẩu, mã hóa & giải mã JWT access token (`app/core/security.py`)

### 2. Mô Hình Dữ Liệu ORM (`app/models/`)
- [x] **User:** id, username, password_hash, full_name, role (`manager` / `staff`), is_active, created_at (`app/models/user.py`)
- [x] **Category:** id, name, description, relationship với Product (`app/models/category.py`)
- [x] **Supplier:** id, name, phone, email, address, relationship với Product (`app/models/supplier.py`)
- [x] **Product:** id, code (unique), name, category_id, supplier_id, unit, min_quantity, current_stock, price, is_active (`app/models/product.py`)
- [x] **ImportOrder & ImportItem:** Quản lý phiếu nhập kho, nhà cung cấp, ngày nhập, tổng tiền, chi tiết số lượng, đơn giá, hạn sử dụng (`app/models/import_order.py`)
- [x] **ExportOrder & ExportItem:** Quản lý phiếu xuất kho, lý do xuất (tiêu thụ/hỏng/hết hạn), người tạo, chi tiết số lượng xuất (`app/models/export_order.py`)
- [x] **Proposal, ProposalItem & ProposalLog:** Quản lý đề xuất nhập hàng (AI/thủ công), các trạng thái workflow, chi tiết lượng đề xuất, tiêu thụ TB/ngày, lý do, mức ưu tiên và timeline lịch sử thao tác (`app/models/proposal.py`)

### 3. Pydantic Schemas Validation (`app/schemas/`)
- [x] **Auth:** `UserOut`, `Token`, `LoginRequest` (`app/schemas/auth.py`)
- [x] **Category:** `CategoryCreate`, `CategoryUpdate`, `CategoryOut` (`app/schemas/category.py`)
- [x] **Supplier:** `SupplierCreate`, `SupplierUpdate`, `SupplierOut` (`app/schemas/supplier.py`)
- [x] **Product:** `ProductCreate`, `ProductUpdate`, `ProductOut` (`app/schemas/product.py`)
- [x] **ImportOrder:** `ImportOrderCreate`, `ImportItemCreate`, `ImportOrderOut`, `ImportItemOut` (`app/schemas/import_order.py`)
- [x] **ExportOrder:** `ExportOrderCreate`, `ExportItemCreate`, `ExportOrderOut`, `ExportItemOut` (`app/schemas/export_order.py`)
- [x] **Proposal:** `ProposalCreate`, `ProposalItemCreate`, `ProposalOut`, `ProposalStatusUpdate`, `AISuggestionOut` (`app/schemas/proposal.py`)

### 4. Dịch Vụ Nghiệp Vụ Cốt Lõi (`app/services/`)
- [x] **AI Service (`app/services/ai_service.py`):**
  - [x] Tính toán lượng tiêu thụ trung bình hàng ngày $D$ từ lịch sử xuất kho 30 ngày gần nhất
  - [x] Triển khai công thức toán học: $Q = \max(0, D \times (L + S) - I)$ với Lead time $L=3$, Safety days $S=7$
  - [x] So khớp mức tồn tối thiểu $min\_quantity$ để đảm bảo hàng không bị cạn
  - [x] Xếp loại mức độ ưu tiên: `HIGH` (dưới ngưỡng tối thiểu/hết hàng), `MEDIUM` (tiêu thụ nhanh), `LOW`
  - [x] Thiết kế Strategy Pattern mở (sẵn sàng kết nối LLM Gemini / AgentX)
- [x] **Workflow Service (`app/services/workflow_service.py`):**
  - [x] Máy trạng thái hữu hạn (State Machine) kiểm soát luồng:
    - `PENDING` $\rightarrow$ `APPROVED` / `REJECTED` / `CANCELLED`
    - `APPROVED` $\rightarrow$ `IN_PROGRESS` / `CANCELLED`
    - `IN_PROGRESS` $\rightarrow$ `COMPLETED` / `CANCELLED`
  - [x] Ghi nhận lịch sử `ProposalLog` (action, actor_id, comment, timestamp)
  - [x] Xử lý tự động khi trạng thái chuyển sang `COMPLETED`: Tự động tạo phiếu nhập kho `PNxxxx` và cộng tăng số lượng tồn kho `Product.current_stock`

### 5. API Routers (`app/routers/`)
- [x] **Middleware & Phân quyền (`app/routers/deps.py`):**
  - [x] `get_current_user`: Xác thực JWT Bearer Token, kiểm tra tài khoản còn hoạt động
  - [x] `require_manager`: Kiểm tra quyền Quản lý (`role == 'manager'`)
- [x] **Xác thực (`app/routers/auth.py`):**
  - [x] `POST /api/auth/login`: Hỗ trợ cả FormData và JSON body, trả JWT access token & user info
  - [x] `GET /api/auth/me`: Lấy thông tin user đăng nhập hiện tại
- [x] **Danh mục (`app/routers/categories.py`):**
  - [x] `GET /api/categories/`: Danh sách danh mục
  - [x] `POST /api/categories/`: Thêm mới (Quản lý)
  - [x] `PUT /api/categories/{id}`: Sửa (Quản lý)
  - [x] `DELETE /api/categories/{id}`: Xóa (Quản lý)
- [x] **Nhà cung cấp (`app/routers/suppliers.py`):**
  - [x] `GET /api/suppliers/`: Danh sách nhà cung cấp
  - [x] `POST /api/suppliers/`: Thêm mới (Quản lý)
  - [x] `PUT /api/suppliers/{id}`: Sửa (Quản lý)
  - [x] `DELETE /api/suppliers/{id}`: Xóa (Quản lý)
- [x] **Hàng hóa (`app/routers/products.py`):**
  - [x] `GET /api/products/`: Lọc theo từ khóa (tên/mã), danh mục, lọc hàng dưới ngưỡng
  - [x] `POST /api/products/`: Thêm hàng hóa, tự động sinh mã `SPxxx` nếu chưa có (Quản lý)
  - [x] `PUT /api/products/{id}`: Cập nhật thông tin hàng hóa (Quản lý)
  - [x] `DELETE /api/products/{id}`: Xóa mềm `is_active = False` (Quản lý)
- [x] **Nhập kho (`app/routers/imports.py`):**
  - [x] `GET /api/imports/`: Lọc theo khoảng ngày
  - [x] `GET /api/imports/{id}`: Chi tiết phiếu nhập & các mặt hàng
  - [x] `POST /api/imports/`: Tạo phiếu nhập, tự động sinh mã `PNxxxx`, tự động cộng tồn kho cho từng sản phẩm
- [x] **Xuất kho (`app/routers/exports.py`):**
  - [x] `GET /api/exports/`: Lọc theo khoảng ngày, lý do
  - [x] `GET /api/exports/{id}`: Chi tiết phiếu xuất
  - [x] `POST /api/exports/`: Kiểm tra tồn kho khả dụng trước khi xuất, báo lỗi 400 nếu không đủ tồn, tự động trừ tồn kho
- [x] **Tồn kho & Dashboard (`app/routers/inventory.py`):**
  - [x] `GET /api/inventory/`: Danh sách tồn kho theo danh mục, tìm kiếm
  - [x] `GET /api/inventory/alerts`: Danh sách các mặt hàng dưới ngưỡng tối thiểu
  - [x] `GET /api/inventory/dashboard`: Thống kê tổng quan (tổng SKU, tổng giá trị tồn kho, số hàng dưới ngưỡng, số đề xuất chờ duyệt, số lượt nhập/xuất trong ngày)
- [x] **Đề xuất & Workflow (`app/routers/proposals.py`):**
  - [x] `POST /api/proposals/ai-analyze`: Gọi AI phân tích tồn kho và trả danh sách đề xuất
  - [x] `POST /api/proposals/`: Tạo đề xuất nhập hàng (AI hoặc thủ công), sinh mã `DXxxxx`
  - [x] `GET /api/proposals/`: Danh sách đề xuất (hỗ trợ lọc theo trạng thái)
  - [x] `GET /api/proposals/{id}`: Chi tiết đề xuất kèm danh sách mặt hàng và nhật ký workflow
  - [x] `PUT /api/proposals/{id}/approve`: Quản lý phê duyệt
  - [x] `PUT /api/proposals/{id}/reject`: Quản lý từ chối
  - [x] `PUT /api/proposals/{id}/start`: Nhân viên bắt đầu liên hệ nhập hàng
  - [x] `PUT /api/proposals/{id}/complete`: Nhân viên hoàn tất nhập hàng (tự động tạo phiếu nhập và cộng tồn)
  - [x] `PUT /api/proposals/{id}/cancel`: Hủy đề xuất
- [x] **Báo cáo (`app/routers/reports.py`):**
  - [x] `GET /api/reports/imports`: Báo cáo nhập kho theo thời gian, tính tổng giá trị
  - [x] `GET /api/reports/exports`: Báo cáo xuất kho, tổng hợp số lượng tiêu thụ theo từng SKU
  - [x] `GET /api/reports/inventory-summary`: Định giá tài sản tồn kho hiện tại theo từng mặt hàng

### 6. Khởi Tạo Dữ Liệu & Kiểm Thử (`seed_data.py` & `test_api.py`)
- [x] **Dữ liệu mẫu thực tế:**
  - 2 tài khoản: Quản lý (`admin / admin123`), Nhân viên (`nhanvien / nv123`)
  - 5 Danh mục, 3 Nhà cung cấp
  - 20 Sản phẩm căng tin thực tế (nước ngọt, mì, bánh kẹo, sữa, đồ dùng)
  - Lịch sử nhập kho & lịch sử xuất kho 30 ngày (đảm bảo AI có đủ dữ liệu tính mức tiêu thụ)
- [x] **Bộ test kiểm thử tự động:**
  - Đã chạy qua `test_api.py` kiểm tra trọn vẹn toàn bộ 8 luồng nghiệp vụ không có bất kỳ lỗi nào.
