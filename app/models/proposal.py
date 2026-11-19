from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="PENDING")
    # PENDING -> APPROVED/REJECTED -> IN_PROGRESS -> COMPLETED/CANCELLED
    ai_generated = Column(Boolean, default=False)
    notes = Column(String(500), default="")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_comment = Column(String(500), default="")

    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    items = relationship("ProposalItem", back_populates="proposal", cascade="all, delete-orphan")
    logs = relationship("ProposalLog", back_populates="proposal", cascade="all, delete-orphan")

class ProposalItem(Base):
    __tablename__ = "proposal_items"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    current_stock = Column(Float, default=0.0)
    suggested_quantity = Column(Float, nullable=False)
    reason = Column(String(500), default="")
    priority = Column(String(10), default="MEDIUM")  # HIGH, MEDIUM, LOW
    daily_consumption = Column(Float, default=0.0)

    proposal = relationship("Proposal", back_populates="items")
    product = relationship("Product")

class ProposalLog(Base):
    __tablename__ = "proposal_logs"

    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    action = Column(String(30), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    proposal = relationship("Proposal", back_populates="logs")
    actor = relationship("User")
