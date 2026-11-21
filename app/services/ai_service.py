"""
AI Service - Phân tích dữ liệu tồn kho & Đề xuất nhập hàng
Mô hình thuật toán: Q = max(0, D * (L + S) - I)
- D: Tiêu thụ trung bình hàng ngày (dựa trên lịch sử xuất kho 30 ngày)
- L: Lead time (Thời gian giao hàng, mặc định 3 ngày)
- S: Safety stock days (Số ngày dự trữ an toàn, mặc định 7 ngày)
- I: Tồn kho hiện tại
Thiết kế mở theo Strategy Pattern để sẵn sàng thay thế/tích hợp thêm LLM Agent (Gemini/AgentX).
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.product import Product
from app.models.export_order import ExportItem, ExportOrder

LEAD_TIME_DAYS = 3
SAFETY_STOCK_DAYS = 7
ANALYSIS_DAYS = 30

def calculate_daily_consumption(db: Session, product_id: int, days: int = ANALYSIS_DAYS) -> float:
    since_date = datetime.utcnow() - timedelta(days=days)
    total_qty = (
        db.query(func.sum(ExportItem.quantity))
        .join(ExportOrder, ExportItem.order_id == ExportOrder.id)
        .filter(
            ExportItem.product_id == product_id,
            ExportOrder.created_at >= since_date
        )
        .scalar()
        or 0.0
    )
    return float(total_qty) / float(days)

def analyze_and_suggest(
    db: Session,
    lead_time: int = LEAD_TIME_DAYS,
    safety_days: int = SAFETY_STOCK_DAYS,
    analysis_days: int = ANALYSIS_DAYS
) -> List[Dict[str, Any]]:
    products = db.query(Product).filter(Product.is_active == True).all()
    suggestions = []

    for product in products:
        d = calculate_daily_consumption(db, product.id, analysis_days)
        i = float(product.current_stock)
        min_qty = float(product.min_quantity)

        # Công thức: Q = max(0, D * (L + S) - I)
        demand_target = d * (lead_time + safety_days)
        q = max(0.0, demand_target - i)

        # Kiểm tra ngưỡng tối thiểu: nếu tồn kho < tồn tối thiểu thì cần nhập ít nhất lên min_qty
        if i < min_qty and (i + q) < min_qty:
            q = min_qty - i

        # Kiểm tra mặt hàng mấp mé ngưỡng an toàn (min_qty <= i < min_qty * 1.25)
        is_near_minimum = (min_qty <= i < min_qty * 1.25)
        if q <= 0 and is_near_minimum and d > 0:
            q = max(round(min_qty * 0.25), 5.0)

        # Nếu tồn kho dồi dào (i >= min_qty * 1.25) và không có nhu cầu bù dự trữ an toàn thì bỏ qua
        if q <= 0 and not is_near_minimum and i >= min_qty:
            continue
        if q <= 0 and i >= min_qty:
            continue

        # Tính số ngày tồn kho khả dụng (Days of Supply)
        days_of_stock = (i / d) if d > 0 else 999.0

        # Phân loại mức độ ưu tiên & lý do giải thích (Explainable AI)
        # 1. 🔴 KHẨN CẤP (HIGH): Hết hàng hoặc tồn kho nguy cấp (<= 50% min_qty hoặc DOS < lead_time)
        if i <= 0:
            priority = "HIGH"
            reason = f"Hết hàng (Tồn 0 {product.unit}), cần nhập khẩn cấp!"
        elif i <= (min_qty * 0.5) or days_of_stock < lead_time:
            priority = "HIGH"
            reason = f"Tồn kho nguy cấp ({i:.1f} {product.unit} ≤ 50% mức tối thiểu), nguy cơ đứt hàng trong {days_of_stock:.1f} ngày!"
        # 2. 🟠 TRUNG BÌNH (MEDIUM): Tồn kho dưới mức tối thiểu nhưng còn cầm cự được, hoặc tiêu thụ tốt cần bù an toàn
        elif i < min_qty:
            priority = "MEDIUM"
            reason = f"Tồn kho ({i:.1f} {product.unit}) dưới mức tối thiểu ({min_qty:.1f} {product.unit}), cần nhập bổ sung."
        elif q > 0 and (demand_target > i):
            priority = "MEDIUM"
            reason = f"Tiêu thụ tốt ({d:.1f} {product.unit}/ngày), cần nhập thêm {q:.0f} {product.unit} để đủ {safety_days} ngày dự trữ an toàn."
        # 3. 🟢 THẤP (LOW): Tồn kho mấp mé an toàn, đề xuất nhập dự phòng sớm
        else:
            priority = "LOW"
            reason = f"Tồn kho ({i:.1f} {product.unit}) mấp mé ngưỡng an toàn ({min_qty:.1f} {product.unit}), đề xuất nhập dự phòng."

        suggestions.append({
            "product_id": product.id,
            "product_name": product.name,
            "product_code": product.code,
            "unit": product.unit,
            "current_stock": round(i, 1),
            "suggested_quantity": round(max(q, 1.0), 1),
            "daily_consumption": round(d, 2),
            "reason": reason,
            "priority": priority,
        })

    # Sắp xếp ưu tiên: HIGH (0) -> MEDIUM (1) -> LOW (2), nếu cùng mức ưu tiên thì ưu tiên lượng cần nhập Q lớn hơn
    priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda item: (priority_map.get(item["priority"], 99), -item["suggested_quantity"]))
    return suggestions
