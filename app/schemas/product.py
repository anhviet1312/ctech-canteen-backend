from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.schemas.category import CategoryOut
from app.schemas.supplier import SupplierOut

class ProductBase(BaseModel):
    name: str
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    unit: str = "cái"
    min_quantity: float = 10.0
    price: float = 0.0
    description: Optional[str] = ""

class ProductCreate(ProductBase):
    code: Optional[str] = None
    current_stock: Optional[float] = 0.0

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    unit: Optional[str] = None
    min_quantity: Optional[float] = None
    price: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductOut(ProductBase):
    id: int
    code: str
    current_stock: float
    is_active: bool
    category: Optional[CategoryOut] = None
    supplier: Optional[SupplierOut] = None

    model_config = ConfigDict(from_attributes=True)

class InventoryItemOut(BaseModel):
    id: int
    product_id: int
    code: str
    product_code: str
    name: str
    product_name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = "—"
    category: Optional[CategoryOut] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = "—"
    supplier: Optional[SupplierOut] = None
    unit: str = "cái"
    min_quantity: float = 10.0
    current_stock: float = 0.0
    price: float = 0.0
    stock_value: float = 0.0
    status: str = "Đủ hàng"
    description: Optional[str] = ""
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
