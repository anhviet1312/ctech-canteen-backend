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

        # Nếu tồn kho vẫn đầy đủ an toàn và không dưới min_qty thì bỏ qua
        if q <= 0 and i >= min_qty:
            continue

        # Xác định mức độ ưu tiên & lý do
        if i <= 0:
            priority = "HIGH"
            reason = f"Hết hàng (Tồn 0 {product.unit}), cần nhập khẩn cấp!"
        elif i < min_qty:
            priority = "HIGH"
            reason = f"Tồn kho ({i:.1f} {product.unit}) dưới mức tối thiểu ({min_qty:.1f} {product.unit})."
        elif q > 0:
            priority = "MEDIUM" if d > 0 else "LOW"
            reason = f"Tiêu thụ TB {d:.1f} {product.unit}/ngày, cần bù để đủ {safety_days} ngày dự trữ an toàn."
        else:
            priority = "LOW"
            reason = f"Tồn kho gần ngưỡng tối thiểu ({min_qty:.1f} {product.unit})."

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

    # Sắp xếp ưu tiên: HIGH -> MEDIUM -> LOW
    priority_map = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    suggestions.sort(key=lambda item: priority_map.get(item["priority"], 99))
    return suggestions
