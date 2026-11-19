from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.product import Product
from app.models.proposal import Proposal
from app.models.import_order import ImportOrder
from app.models.export_order import ExportOrder
from app.schemas.product import ProductOut, InventoryItemOut
from app.routers.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[InventoryItemOut])
def get_inventory(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Product).filter(Product.is_active == True)
    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            (Product.name.ilike(search_filter)) | (Product.code.ilike(search_filter))
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)

    products = query.order_by(Product.id.asc()).all()
    results = []
    for p in products:
        cat_name = p.category.name if p.category else "—"
        sup_name = p.supplier.name if p.supplier else "—"
        val = round(p.current_stock * p.price, 0)
        status = "Dưới ngưỡng" if p.current_stock < p.min_quantity else "Đủ hàng"
        results.append({
            "id": p.id,
            "product_id": p.id,
            "code": p.code,
            "product_code": p.code,
            "name": p.name,
            "product_name": p.name,
            "category_id": p.category_id,
            "category_name": cat_name,
            "category": p.category,
            "supplier_id": p.supplier_id,
            "supplier_name": sup_name,
            "supplier": p.supplier,
            "unit": p.unit,
            "min_quantity": p.min_quantity,
            "current_stock": p.current_stock,
            "price": p.price,
            "stock_value": val,
            "status": status,
            "description": p.description or "",
            "is_active": p.is_active
        })
    return results

@router.get("/alerts", response_model=List[InventoryItemOut])
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Trả về các mặt hàng có tồn kho dưới mức tối thiểu
    products = db.query(Product).filter(
        Product.is_active == True,
        Product.current_stock < Product.min_quantity
    ).order_by(Product.current_stock.asc()).all()

    results = []
    for p in products:
        cat_name = p.category.name if p.category else "—"
        sup_name = p.supplier.name if p.supplier else "—"
        val = round(p.current_stock * p.price, 0)
        results.append({
            "id": p.id,
            "product_id": p.id,
            "code": p.code,
            "product_code": p.code,
            "name": p.name,
            "product_name": p.name,
            "category_id": p.category_id,
            "category_name": cat_name,
            "category": p.category,
            "supplier_id": p.supplier_id,
            "supplier_name": sup_name,
            "supplier": p.supplier,
            "unit": p.unit,
            "min_quantity": p.min_quantity,
            "current_stock": p.current_stock,
            "price": p.price,
            "stock_value": val,
            "status": "Dưới ngưỡng",
            "description": p.description or "",
            "is_active": p.is_active
        })
    return results

@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    products = db.query(Product).filter(Product.is_active == True).all()
    total_products = len(products)
    total_stock_value = sum(p.current_stock * p.price for p in products)
    low_stock_count = sum(1 for p in products if p.current_stock < p.min_quantity)

    pending_proposals = db.query(Proposal).filter(Proposal.status == "PENDING").count()

    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())

    today_imports = db.query(ImportOrder).filter(
        ImportOrder.created_at >= today_start,
        ImportOrder.created_at <= today_end
    ).count()

    today_exports = db.query(ExportOrder).filter(
        ExportOrder.created_at >= today_start,
        ExportOrder.created_at <= today_end
    ).count()

    return {
        "total_products": total_products,
        "total_stock_value": round(total_stock_value, 0),
        "low_stock_count": low_stock_count,
        "pending_proposals": pending_proposals,
        "today_imports": today_imports,
        "today_exports": today_exports
    }
