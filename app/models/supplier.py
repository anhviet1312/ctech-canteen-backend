from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), default="")
    email = Column(String(100), default="")
    address = Column(String(255), default="")
    products = relationship("Product", back_populates="supplier")
