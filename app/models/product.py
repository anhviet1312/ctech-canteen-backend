from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    unit = Column(String(30), nullable=False, default="cái")
    min_quantity = Column(Float, default=10.0)
    current_stock = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    description = Column(String(255), default="")
    is_active = Column(Boolean, default=True)

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
