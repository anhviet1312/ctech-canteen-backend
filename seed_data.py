"""
Seed data script for CTECH Canteen Inventory Management System
Chạy: python seed_data.py
Tạo 2 tài khoản, 5 danh mục, 3 nhà cung cấp, 20 sản phẩm và lịch sử nhập/xuất 30 ngày
"""
import sys
import os
from datetime import datetime, timedelta, date

# Set UTF-8 encoding for standard output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thêm thư mục gốc backend vào sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.category import Category
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.import_order import ImportOrder, ImportItem
from app.models.export_order import ExportOrder, ExportItem
from app.models.proposal import Proposal, ProposalItem, ProposalLog

def seed():
    print("🚀 Đang khởi tạo cơ sở dữ liệu SQLite...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Kiểm tra nếu đã có dữ liệu thì xóa hoặc bỏ qua
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️ Dữ liệu đã tồn tại trong database. Đang làm mới dữ liệu mẫu...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)

        print("1️⃣ Đang tạo tài khoản người dùng...")
        users = [
            User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                full_name="Nguyễn Văn Quản Lý",
                role="manager",
                is_active=True
            ),
            User(
                username="nhanvien",
                password_hash=get_password_hash("nv123"),
                full_name="Trần Thị Nhân Viên",
                role="staff",
                is_active=True
            )
        ]
        db.add_all(users)
        db.commit()
        admin_user = users[0]
        staff_user = users[1]

        print("2️⃣ Đang tạo danh mục hàng hóa...")
        categories = [
            Category(name="Nước giải khát", description="Nước ngọt, nước suối, trà đóng chai, nước tăng lực"),
            Category(name="Bánh kẹo & Snack", description="Snack, bánh quy, kẹo ngậm các loại"),
            Category(name="Mì & Thức ăn nhanh", description="Mì gói, mì ly, xúc xích ăn liền"),
            Category(name="Sữa & Đồ uống dinh dưỡng", description="Sữa tươi, sữa chua, sữa hạt"),
            Category(name="Đồ dùng căng tin", description="Ly giấy, ống hút, khăn giấy, cốc dùng một lần")
        ]
        db.add_all(categories)
        db.commit()

        print("3️⃣ Đang tạo nhà cung cấp...")
        suppliers = [
            Supplier(
                name="Công ty TNHH Thực Phẩm Minh Châu",
                phone="0901234567",
                email="minhchau.food@gmail.com",
                address="Số 45 Đường Giải Phóng, Hà Nội"
            ),
            Supplier(
                name="Nhà phân phối Bách Hóa Phúc Thịnh",
                phone="0912345678",
                email="phucthinh.dist@canteen.vn",
                address="Số 12 Ngõ 88 Cầu Giấy, Hà Nội"
            ),
            Supplier(
                name="Đại lý Bao bì & Tiêu hao Nam Anh",
                phone="0923456789",
                email="namanh.packaging@gmail.com",
                address="Cụm công nghiệp Nam Thăng Long, Hà Nội"
            )
        ]
        db.add_all(suppliers)
        db.commit()

        print("4️⃣ Đang tạo 20 mặt hàng thực tế của Căng tin CTECH...")
        products_data = [
            # Nước giải khát (cat 0, sup 0/1)
            ("SP001", "Nước ngọt Coca-Cola 320ml", 1, 1, "lon", 24.0, 18.0, 8500.0, "Nước ngọt có ga lon"), # MEDIUM (75% min)
            ("SP002", "Nước ngọt Pepsi 320ml", 1, 1, "lon", 24.0, 8.0, 8500.0, "Nước ngọt Pepsi lon"), # HIGH (nguy cấp < 50% min)
            ("SP003", "Nước khoáng Aquafina 500ml", 1, 1, "chai", 48.0, 0.0, 5000.0, "Nước lọc tinh khiết"), # HIGH (hết hàng)
            ("SP004", "Nước tăng lực Redbull 250ml", 1, 2, "lon", 24.0, 30.0, 12000.0, "Nước tăng lực lon"), # SAFE (dồi dào)
            ("SP005", "Trà xanh Không Độ 455ml", 1, 2, "chai", 24.0, 4.0, 8000.0, "Trà xanh đóng chai"), # HIGH (nguy cấp < 50% min)
            ("SP006", "Trà Ô Long TEA+ 455ml", 1, 2, "chai", 24.0, 26.0, 9000.0, "Trà Ô Long không đường"), # LOW (mấp mé an toàn 26/24)
            # Bánh kẹo & Snack (cat 1, sup 1)
            ("SP007", "Snack Oishi Cay Nồng 40g", 2, 2, "gói", 30.0, 6.0, 6000.0, "Snack ăn vặt học sinh"), # HIGH (nguy cấp)
            ("SP008", "Snack khoai tây Lay's 52g", 2, 2, "gói", 25.0, 20.0, 11000.0, "Bánh khoai tây chiên"), # MEDIUM (80% min)
            ("SP009", "Bánh quy AFC Lúa Mì 172g", 2, 2, "hộp", 20.0, 28.0, 16000.0, "Bánh quy dinh dưỡng"), # SAFE (dồi dào)
            ("SP010", "Bánh Chocopie Lotte 6 cái", 2, 2, "hộp", 15.0, 4.0, 24000.0, "Bánh phủ sô cô la"), # HIGH (nguy cấp)
            ("SP011", "Kẹo cao su Doublemint", 2, 2, "thanh", 40.0, 50.0, 5000.0, "Kẹo bạc hà the mát"), # SAFE (dồi dào)
            # Mì & Thức ăn nhanh (cat 2, sup 0)
            ("SP012", "Mì Hảo Hảo Tôm chua cay 75g", 3, 1, "gói", 60.0, 18.0, 4200.0, "Mì ăn liền phổ biến"), # HIGH (nguy cấp)
            ("SP013", "Mì ly Omachi Bò Hầm 68g", 3, 1, "ly", 36.0, 24.0, 9500.0, "Mì khoai tây có thịt"), # MEDIUM (66% min)
            ("SP014", "Xúc xích tiệt trùng CP 4 cây", 3, 1, "gói", 30.0, 32.0, 14000.0, "Xúc xích ăn kèm mì"), # LOW (mấp mé an toàn 32/30)
            ("SP015", "Bánh mì sandwich bơ sữa", 3, 1, "cái", 20.0, 5.0, 12000.0, "Bánh mì tươi buổi sáng"), # HIGH (nguy cấp)
            # Sữa & Dinh dưỡng (cat 3, sup 1)
            ("SP016", "Sữa tươi Vinamilk có đường 180ml", 4, 2, "hộp", 48.0, 34.0, 7800.0, "Sữa tươi tiệt trùng"), # MEDIUM (70% min)
            ("SP017", "Sữa cacao lúa mạch Milo 180ml", 4, 2, "hộp", 36.0, 40.0, 8500.0, "Sữa Milo năng lượng"), # LOW (mấp mé an toàn 40/36)
            ("SP018", "Sữa chua ăn Vinamilk có đường", 4, 2, "hộp", 30.0, 8.0, 6500.0, "Sữa chua hộp làm mát"), # HIGH (nguy cấp)
            # Đồ dùng căng tin (cat 4, sup 2)
            ("SP019", "Cốc giấy dùng 1 lần 250ml", 5, 3, "cây", 20.0, 25.0, 35000.0, "Cây 50 cốc giấy"), # SAFE (dồi dào)
            ("SP020", "Khăn giấy napkin Pulppy", 5, 3, "gói", 15.0, 18.0, 15000.0, "Khăn giấy ăn căng tin") # SAFE (dồi dào)
        ]

        products = []
        for code, name, cat_idx, sup_idx, unit, min_q, stock, price, desc in products_data:
            p = Product(
                code=code,
                name=name,
                category_id=cat_idx,
                supplier_id=sup_idx,
                unit=unit,
                min_quantity=min_q,
                current_stock=stock,
                price=price,
                description=desc,
                is_active=True
            )
            products.append(p)
            db.add(p)
        db.commit()

        print("5️⃣ Đang tạo lịch sử Nhập kho & Xuất kho 30 ngày...")
        now = datetime.utcnow()

        # Tạo các phiếu nhập lịch sử
        import_history = [
            (30, 1, [("SP001", 50, 8500), ("SP002", 50, 8500), ("SP003", 100, 5000), ("SP012", 100, 4200)]),
            (20, 2, [("SP004", 48, 12000), ("SP007", 60, 6000), ("SP016", 72, 7800), ("SP017", 72, 8500)]),
            (10, 1, [("SP001", 30, 8500), ("SP005", 30, 8000), ("SP013", 48, 9500), ("SP014", 50, 14000)]),
            (4, 3, [("SP019", 30, 35000), ("SP020", 25, 15000)])
        ]

        for idx, (days_ago, sup_id, items_info) in enumerate(import_history, start=1):
            created_time = now - timedelta(days=days_ago)
            total = sum(q * p for _, q, p in items_info)
            imp_order = ImportOrder(
                code=f"PN{idx:04d}",
                supplier_id=sup_id,
                created_by=staff_user.id,
                created_at=created_time,
                notes=f"Nhập hàng định kỳ đợt cách đây {days_ago} ngày",
                total_amount=total
            )
            db.add(imp_order)
            db.flush()

            for pcode, qty, unit_pr in items_info:
                prd = next(p for p in products if p.code == pcode)
                db.add(ImportItem(
                    order_id=imp_order.id,
                    product_id=prd.id,
                    quantity=qty,
                    unit_price=unit_pr,
                    expiry_date=(date.today() + timedelta(days=90))
                ))
        db.commit()

        # Tạo các phiếu xuất kho hàng ngày trong 30 ngày để tạo dữ liệu tiêu thụ cho AI
        export_daily_pattern = [
            ("SP001", 3.0),
            ("SP002", 3.5),
            ("SP003", 6.0),
            ("SP004", 2.0),
            ("SP005", 2.5),
            ("SP006", 1.5),
            ("SP007", 4.0),
            ("SP008", 2.0),
            ("SP009", 1.5),
            ("SP010", 2.0),
            ("SP012", 6.5),
            ("SP013", 3.0),
            ("SP014", 2.5),
            ("SP015", 3.0),
            ("SP016", 4.5),
            ("SP017", 3.0),
            ("SP018", 2.0),
        ]

        exp_counter = 1
        for day in range(28, 0, -3):
            created_time = now - timedelta(days=day)
            exp_order = ExportOrder(
                code=f"PX{exp_counter:04d}",
                created_by=staff_user.id,
                created_at=created_time,
                reason="consumption",
                notes=f"Xuất hàng phục vụ tiêu thụ tại quầy căng tin ngày {created_time.strftime('%d/%m')}"
            )
            db.add(exp_order)
            db.flush()
            exp_counter += 1

            for pcode, daily_rate in export_daily_pattern:
                prd = next(p for p in products if p.code == pcode)
                qty = round(daily_rate * 3.0, 1)  # xuất cho 3 ngày
                db.add(ExportItem(
                    order_id=exp_order.id,
                    product_id=prd.id,
                    quantity=qty
                ))
        db.commit()

        print("6️⃣ Đang tạo 1 đề xuất mẫu đã phê duyệt...")
        proposal_sample = Proposal(
            code="DX0001",
            created_by=staff_user.id,
            created_at=now - timedelta(days=2),
            status="APPROVED",
            ai_generated=True,
            notes="Đề xuất tự động từ phân tích AI: Bổ sung các mặt hàng tiêu thụ nhanh trước cuối tuần",
            reviewed_by=admin_user.id,
            reviewed_at=now - timedelta(days=1),
            review_comment="Đã xem xét và đồng ý số lượng đề xuất. Nhân viên tiến hành liên hệ nhà cung cấp."
        )
        db.add(proposal_sample)
        db.flush()

        prop_items_data = [
            ("SP003", 12.0, 50.0, "Nhu cầu cao mùa nắng, tồn kho sắp cạn", "HIGH", 6.0),
            ("SP005", 5.0, 30.0, "Tồn kho dưới ngưỡng tối thiểu", "HIGH", 2.5),
            ("SP012", 18.0, 60.0, "Tiêu thụ trung bình 6.5 gói/ngày", "HIGH", 6.5),
        ]
        for pcode, cur_stk, sug_q, rsn, pri, dcon in prop_items_data:
            prd = next(p for p in products if p.code == pcode)
            db.add(ProposalItem(
                proposal_id=proposal_sample.id,
                product_id=prd.id,
                current_stock=cur_stk,
                suggested_quantity=sug_q,
                reason=rsn,
                priority=pri,
                daily_consumption=dcon
            ))

        db.add(ProposalLog(
            proposal_id=proposal_sample.id,
            action="CREATED",
            actor_id=staff_user.id,
            comment="Khởi tạo đề xuất từ AI Agent",
            created_at=now - timedelta(days=2)
        ))
        db.add(ProposalLog(
            proposal_id=proposal_sample.id,
            action="APPROVED",
            actor_id=admin_user.id,
            comment="Quản lý phê duyệt đề xuất",
            created_at=now - timedelta(days=1)
        ))
        db.commit()

        print("✅ KHỞI TẠO DỮ LIỆU THÀNH CÔNG!")
        print("--------------------------------------------------")
        print("Tài khoản Quản lý:   admin    / admin123")
        print("Tài khoản Nhân viên: nhanvien / nv123")
        print("--------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi khi khởi tạo dữ liệu: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed()
