from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base

class ImportOrder(Base):
    __tablename__ = "import_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String(500), default="")
    total_amount = Column(Float, default=0.0)
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)

    supplier = relationship("Supplier")
    creator = relationship("User")
    items = relationship("ImportItem", back_populates="order", cascade="all, delete-orphan")

class ImportItem(Base):
    __tablename__ = "import_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("import_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, default=0.0)
    expiry_date = Column(Date, nullable=True)

    order = relationship("ImportOrder", back_populates="items")
    product = relationship("Product")
