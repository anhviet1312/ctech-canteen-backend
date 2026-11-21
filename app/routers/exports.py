from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.export_order import ExportOrder, ExportItem
from app.models.product import Product
from app.schemas.export_order import ExportOrderCreate, ExportOrderOut
from app.routers.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ExportOrderOut])
def get_exports(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    reason: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ExportOrder)
    if date_from:
        query = query.filter(ExportOrder.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(ExportOrder.created_at <= datetime.combine(date_to, datetime.max.time()))
    if reason:
        query = query.filter(ExportOrder.reason == reason)

    return query.order_by(ExportOrder.id.desc()).all()

@router.get("/{order_id}", response_model=ExportOrderOut)
def get_export_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ExportOrder).filter(ExportOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu xuất kho")
    return order

@router.post("/", response_model=ExportOrderOut, status_code=status.HTTP_201_CREATED)
def create_export(
    payload: ExportOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phiếu xuất phải có ít nhất 1 mặt hàng")

    # 1. Kiểm tra trùng lặp mặt hàng trong phiếu xuất
    product_ids = [item.product_id for item in payload.items]
    if len(product_ids) != len(set(product_ids)):
        seen = set()
        duplicates = set()
        for pid in product_ids:
            if pid in seen:
                duplicates.add(pid)
            seen.add(pid)
        dup_prods = db.query(Product).filter(Product.id.in_(duplicates)).all()
        dup_names = ", ".join([f"'{p.name}'" for p in dup_prods])
        raise HTTPException(
            status_code=400,
            detail=f"Mặt hàng {dup_names} bị trùng lặp trong phiếu xuất. Vui lòng gộp số lượng vào cùng một dòng."
        )

    # 2. Tính tổng số lượng xuất theo từng mặt hàng và kiểm tra tồn kho khả dụng
    qty_by_product = {}
    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Số lượng xuất phải lớn hơn 0")
        qty_by_product[item.product_id] = qty_by_product.get(item.product_id, 0) + item.quantity

    for prod_id, total_qty in qty_by_product.items():
        prod = db.query(Product).filter(Product.id == prod_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy sản phẩm id {prod_id}")
        if prod.current_stock < total_qty:
            raise HTTPException(
                status_code=400,
                detail=f"Mặt hàng '{prod.name}' tồn kho khả dụng ({prod.current_stock} {prod.unit}) không đủ để xuất ({total_qty} {prod.unit})"
            )

    # Generate Code
    last_order = db.query(ExportOrder).order_by(ExportOrder.id.desc()).first()
    next_id = (last_order.id + 1) if last_order else 1
    code = f"PX{next_id:04d}"

    order = ExportOrder(
        code=code,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        reason=payload.reason,
        notes=payload.notes or ""
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if prod.current_stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Lỗi tồn kho: Mặt hàng '{prod.name}' không đủ để xuất!"
            )
        export_item = ExportItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(export_item)

        # Cập nhật giảm số lượng tồn kho (đảm bảo không âm)
        prod.current_stock = max(0.0, prod.current_stock - item.quantity)

    db.commit()
    db.refresh(order)
    return order
