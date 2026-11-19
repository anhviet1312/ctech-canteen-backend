from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.import_order import ImportOrder, ImportItem
from app.models.product import Product
from app.models.proposal import Proposal
from app.schemas.import_order import ImportOrderCreate, ImportOrderOut
from app.routers.deps import get_current_user
from app.models.user import User
from app.services.workflow_service import transition_proposal

router = APIRouter()

@router.get("/", response_model=List[ImportOrderOut])
def get_imports(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(ImportOrder)
    if date_from:
        query = query.filter(ImportOrder.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(ImportOrder.created_at <= datetime.combine(date_to, datetime.max.time()))

    return query.order_by(ImportOrder.id.desc()).all()

@router.get("/{order_id}", response_model=ImportOrderOut)
def get_import_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(ImportOrder).filter(ImportOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu nhập kho")
    return order

@router.post("/", response_model=ImportOrderOut, status_code=status.HTTP_201_CREATED)
def create_import(
    payload: ImportOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Phiếu nhập phải có ít nhất 1 mặt hàng")

    # Generate Code
    last_order = db.query(ImportOrder).order_by(ImportOrder.id.desc()).first()
    next_id = (last_order.id + 1) if last_order else 1
    code = f"PN{next_id:04d}"

    total_amount = 0.0
    for item in payload.items:
        total_amount += (item.quantity * item.unit_price)

    order = ImportOrder(
        code=code,
        supplier_id=payload.supplier_id,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        notes=payload.notes or "",
        total_amount=total_amount,
        proposal_id=payload.proposal_id
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy sản phẩm id {item.product_id}")

        import_item = ImportItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            expiry_date=item.expiry_date
        )
        db.add(import_item)

        # Cập nhật tăng số lượng tồn kho
        prod.current_stock += item.quantity

    # Nếu phiếu nhập liên kết với đề xuất đang thực hiện, hoàn thành đề xuất
    if payload.proposal_id:
        prop = db.query(Proposal).filter(Proposal.id == payload.proposal_id).first()
        if prop and prop.status == "IN_PROGRESS":
            transition_proposal(
                db=db,
                proposal=prop,
                new_status="COMPLETED",
                actor_id=current_user.id,
                comment=f"Đã lập phiếu nhập kho {code}"
            )

    db.commit()
    db.refresh(order)
    return order
