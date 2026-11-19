from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ExportOrder(Base):
    __tablename__ = "export_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(50), default="consumption")  # consumption, damage, expired, other
    notes = Column(String(500), default="")

    creator = relationship("User")
    items = relationship("ExportItem", back_populates="order", cascade="all, delete-orphan")

class ExportItem(Base):
    __tablename__ = "export_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("export_orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)

    order = relationship("ExportOrder", back_populates="items")
    product = relationship("Product")
