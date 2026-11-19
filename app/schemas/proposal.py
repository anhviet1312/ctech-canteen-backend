from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.auth import UserOut
from app.schemas.product import ProductOut

class ProposalItemCreate(BaseModel):
    product_id: int
    current_stock: Optional[float] = 0.0
    suggested_quantity: float
    reason: Optional[str] = ""
    priority: str = "MEDIUM"
    daily_consumption: Optional[float] = 0.0

class ProposalItemOut(BaseModel):
    id: int
    proposal_id: int
    product_id: int
    current_stock: float
    suggested_quantity: float
    reason: str
    priority: str
    daily_consumption: float
    product: Optional[ProductOut] = None

    model_config = ConfigDict(from_attributes=True)

class ProposalLogOut(BaseModel):
    id: int
    proposal_id: int
    action: str
    actor_id: int
    comment: str
    created_at: datetime
    actor: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)

class ProposalCreate(BaseModel):
    notes: Optional[str] = ""
    ai_generated: bool = False
    items: List[ProposalItemCreate]

class ProposalStatusUpdate(BaseModel):
    comment: Optional[str] = ""

class ProposalOut(BaseModel):
    id: int
    code: str
    created_by: int
    created_at: datetime
    status: str
    ai_generated: bool
    notes: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_comment: str
    creator: Optional[UserOut] = None
    reviewer: Optional[UserOut] = None
    items: List[ProposalItemOut] = []
    logs: List[ProposalLogOut] = []

    model_config = ConfigDict(from_attributes=True)

class AISuggestionOut(BaseModel):
    product_id: int
    product_name: str
    product_code: str
    unit: str
    current_stock: float
    suggested_quantity: float
    daily_consumption: float
    reason: str
    priority: str
