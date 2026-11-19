from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.import_order import ImportOrder, ImportItem
from app.models.export_order import ExportOrder, ExportItem
from app.models.product import Product
from app.models.category import Category
from app.routers.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/imports")
def get_import_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ImportOrder)
    d_from = date_from or start_date
    d_to = date_to or end_date

    if d_from:
        query = query.filter(ImportOrder.created_at >= datetime.combine(d_from, datetime.min.time()))
    if d_to:
        query = query.filter(ImportOrder.created_at <= datetime.combine(d_to, datetime.max.time()))

    orders = query.order_by(ImportOrder.id.desc()).all()
    total_orders = len(orders)
    grand_total_amount = sum(o.total_amount for o in orders)

    items_data = []
    for order in orders:
        items_data.append({
            "id": order.id,
            "code": order.code,
            "supplier": {
                "id": order.supplier.id,
                "name": order.supplier.name
            } if order.supplier else None,
            "supplier_name": order.supplier.name if order.supplier else "N/A",
            "created_at": order.created_at.isoformat(),
            "creator": {
                "id": order.creator.id,
                "full_name": order.creator.full_name
            } if order.creator else None,
            "creator_name": order.creator.full_name if order.creator else "N/A",
            "total_amount": order.total_amount,
            "items": [{"id": it.id, "product_id": it.product_id, "quantity": it.quantity} for it in order.items],
            "item_count": len(order.items),
            "notes": order.notes
        })

    return {
        "total_orders": total_orders,
        "grand_total_amount": grand_total_amount,
        "orders": items_data
    }

@router.get("/exports")
def get_export_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ExportOrder)
    d_from = date_from or start_date
    d_to = date_to or end_date

    if d_from:
        query = query.filter(ExportOrder.created_at >= datetime.combine(d_from, datetime.min.time()))
    if d_to:
        query = query.filter(ExportOrder.created_at <= datetime.combine(d_to, datetime.max.time()))

    orders = query.order_by(ExportOrder.id.desc()).all()
    total_orders = len(orders)

    # Thống kê lượng xuất theo từng sản phẩm
    product_stats: Dict[int, Dict[str, Any]] = {}
    for o in orders:
        for item in o.items:
            prod_id = item.product_id
            if prod_id not in product_stats:
                cat_name = ""
                if item.product and item.product.category:
                    cat_name = item.product.category.name
                product_stats[prod_id] = {
                    "product_id": prod_id,
                    "product_code": item.product.code if item.product else "",
                    "product_name": item.product.name if item.product else "N/A",
                    "category_name": cat_name,
                    "unit": item.product.unit if item.product else "",
                    "total_quantity": 0.0,
                    "export_count": 0,
                    "order_count": 0
                }
            product_stats[prod_id]["total_quantity"] += item.quantity
            product_stats[prod_id]["export_count"] += 1
            product_stats[prod_id]["order_count"] += 1

    return {
        "total_orders": total_orders,
        "products_summary": sorted(list(product_stats.values()), key=lambda x: x["total_quantity"], reverse=True)
    }

@router.get("/inventory-summary")
def get_inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    products = db.query(Product).filter(Product.is_active == True).all()
    summary = []
    total_inventory_value = 0.0

    for p in products:
        value = p.current_stock * p.price
        total_inventory_value += value
        cat_name = p.category.name if p.category else "Chưa phân loại"
        summary.append({
            "id": p.id,
            "code": p.code,
            "product_code": p.code,
            "name": p.name,
            "product_name": p.name,
            "category_name": cat_name,
            "unit": p.unit,
            "current_stock": p.current_stock,
            "min_quantity": p.min_quantity,
            "price": p.price,
            "stock_value": value,
            "status": "Dưới ngưỡng" if p.current_stock < p.min_quantity else "Đủ hàng"
        })

    summary.sort(key=lambda x: x["stock_value"], reverse=True)
    return {
        "total_sku": len(products),
        "total_value": total_inventory_value,
        "items": summary
    }
