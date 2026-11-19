from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut
from app.routers.deps import get_current_user, require_manager
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ProductOut])
def get_products(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    low_stock: Optional[bool] = Query(None),
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

    if low_stock:
        query = query.filter(Product.current_stock < Product.min_quantity)

    return query.order_by(Product.id.asc()).all()

@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    # Auto-generate code if not provided
    code = payload.code
    if not code:
        last_product = db.query(Product).order_by(Product.id.desc()).first()
        next_id = (last_product.id + 1) if last_product else 1
        code = f"SP{next_id:03d}"
    else:
        # Check duplicate
        if db.query(Product).filter(Product.code == code).first():
            raise HTTPException(status_code=400, detail=f"Mã hàng '{code}' đã tồn tại")

    product = Product(
        code=code,
        name=payload.name,
        category_id=payload.category_id,
        supplier_id=payload.supplier_id,
        unit=payload.unit,
        min_quantity=payload.min_quantity,
        current_stock=payload.current_stock or 0.0,
        price=payload.price,
        description=payload.description or "",
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{prod_id}", response_model=ProductOut)
def update_product(
    prod_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    product = db.query(Product).filter(Product.id == prod_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy hàng hóa")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

@router.delete("/{prod_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    prod_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    product = db.query(Product).filter(Product.id == prod_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Không tìm thấy hàng hóa")

    # Soft delete
    product.is_active = False
    db.commit()
    return None
