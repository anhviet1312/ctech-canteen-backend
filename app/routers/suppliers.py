from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierOut
from app.routers.deps import get_current_user, require_manager
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[SupplierOut])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Supplier).order_by(Supplier.id.asc()).all()

@router.post("/", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    supp = Supplier(
        name=payload.name,
        phone=payload.phone or "",
        email=payload.email or "",
        address=payload.address or ""
    )
    db.add(supp)
    db.commit()
    db.refresh(supp)
    return supp

@router.put("/{supp_id}", response_model=SupplierOut)
def update_supplier(
    supp_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    supp = db.query(Supplier).filter(Supplier.id == supp_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    supp.name = payload.name
    if payload.phone is not None:
        supp.phone = payload.phone
    if payload.email is not None:
        supp.email = payload.email
    if payload.address is not None:
        supp.address = payload.address
    db.commit()
    db.refresh(supp)
    return supp

@router.delete("/{supp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    supp = db.query(Supplier).filter(Supplier.id == supp_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    db.delete(supp)
    db.commit()
    return None
