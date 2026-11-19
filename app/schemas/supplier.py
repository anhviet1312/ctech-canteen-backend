from pydantic import BaseModel, ConfigDict
from typing import Optional

class SupplierBase(BaseModel):
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    address: Optional[str] = ""

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    pass

class SupplierOut(SupplierBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
