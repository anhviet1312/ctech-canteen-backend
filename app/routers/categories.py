from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.routers.deps import get_current_user, require_manager
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[CategoryOut])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Category).order_by(Category.id.asc()).all()

@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    cat = Category(name=payload.name, description=payload.description or "")
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/{cat_id}", response_model=CategoryOut)
def update_category(
    cat_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")
    cat.name = payload.name
    if payload.description is not None:
        cat.description = payload.description
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Không tìm thấy danh mục")
    db.delete(cat)
    db.commit()
    return None
