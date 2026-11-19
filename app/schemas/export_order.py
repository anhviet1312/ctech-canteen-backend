from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.auth import UserOut
from app.schemas.product import ProductOut

class ExportItemCreate(BaseModel):
    product_id: int
    quantity: float

class ExportItemOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: float
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)

class ExportOrderCreate(BaseModel):
    reason: str = "consumption"
    notes: Optional[str] = ""
    items: List[ExportItemCreate]

class ExportOrderOut(BaseModel):
    id: int
    code: str
    created_by: int
    created_at: datetime
    reason: str
    notes: str
    creator: Optional[UserOut] = None
    items: List[ExportItemOut] = []

    model_config = ConfigDict(from_attributes=True)
