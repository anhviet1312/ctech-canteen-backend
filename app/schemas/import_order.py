from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from app.schemas.auth import UserOut
from app.schemas.supplier import SupplierOut
from app.schemas.product import ProductOut

class ImportItemCreate(BaseModel):
    product_id: int
    quantity: float
    unit_price: float = 0.0
    expiry_date: Optional[date] = None

class ImportItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: float
    unit_price: float
    expiry_date: Optional[date] = None
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)

class ImportOrderCreate(BaseModel):
    supplier_id: Optional[int] = None
    notes: Optional[str] = ""
    proposal_id: Optional[int] = None
    items: List[ImportItemCreate]

class ImportOrderOut(BaseModel):
    id: int
    code: str
    supplier_id: Optional[int] = None
    created_by: int
    created_at: datetime
    notes: str
    total_amount: float
    proposal_id: Optional[int] = None
    supplier: Optional[SupplierOut] = None
    creator: Optional[UserOut] = None
    items: List[ImportItemOut] = []

    model_config = ConfigDict(from_attributes=True)
