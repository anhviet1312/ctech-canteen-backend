from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.proposal import Proposal, ProposalItem, ProposalLog
from app.models.product import Product
from app.schemas.proposal import (
    ProposalCreate,
    ProposalOut,
    ProposalStatusUpdate,
    AISuggestionOut
)
from app.routers.deps import get_current_user, require_manager
from app.models.user import User
from app.services.ai_service import analyze_and_suggest, calculate_daily_consumption
from app.services.workflow_service import transition_proposal

router = APIRouter()

@router.get("/", response_model=List[ProposalOut])
def get_proposals(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Proposal)
    if status and status != "ALL":
        query = query.filter(Proposal.status == status)

    return query.order_by(Proposal.id.desc()).all()

@router.post("/ai-analyze", response_model=List[AISuggestionOut])
def run_ai_analyze(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chạy phân tích AI đề xuất nhập hàng (không lưu vào DB).
    """
    return analyze_and_suggest(db)

@router.get("/{prop_id}", response_model=ProposalOut)
def get_proposal_detail(
    prop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất nhập hàng")
    return prop

@router.post("/", response_model=ProposalOut, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Đề xuất phải có ít nhất 1 mặt hàng")

    # Sinh mã đề xuất: DX0001
    last_prop = db.query(Proposal).order_by(Proposal.id.desc()).first()
    next_id = (last_prop.id + 1) if last_prop else 1
    code = f"DX{next_id:04d}"

    proposal = Proposal(
        code=code,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        status="PENDING",
        ai_generated=payload.ai_generated,
        notes=payload.notes or ""
    )
    db.add(proposal)
    db.flush()

    for item in payload.items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        daily_con = item.daily_consumption
        if not daily_con or daily_con <= 0.0:
            daily_con = round(calculate_daily_consumption(db, item.product_id, 30), 2)

        prop_item = ProposalItem(
            proposal_id=proposal.id,
            product_id=item.product_id,
            current_stock=prod.current_stock if prod else (item.current_stock or 0.0),
            suggested_quantity=item.suggested_quantity,
            reason=item.reason or "",
            priority=item.priority or "MEDIUM",
            daily_consumption=daily_con or 0.0
        )
        db.add(prop_item)

    # Ghi log khởi tạo
    log = ProposalLog(
        proposal_id=proposal.id,
        action="CREATED",
        actor_id=current_user.id,
        comment="Tạo đề xuất nhập hàng mới" + (" (do AI đề xuất)" if payload.ai_generated else ""),
        created_at=datetime.utcnow()
    )
    db.add(log)

    db.commit()
    db.refresh(proposal)
    return proposal

@router.put("/{prop_id}/approve", response_model=ProposalOut)
def approve_proposal(
    prop_id: int,
    payload: ProposalStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    try:
        return transition_proposal(
            db=db,
            proposal=prop,
            new_status="APPROVED",
            actor_id=current_user.id,
            comment=payload.comment or "Quản lý đã phê duyệt đề xuất"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{prop_id}/reject", response_model=ProposalOut)
def reject_proposal(
    prop_id: int,
    payload: ProposalStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    try:
        return transition_proposal(
            db=db,
            proposal=prop,
            new_status="REJECTED",
            actor_id=current_user.id,
            comment=payload.comment or "Quản lý từ chối đề xuất"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{prop_id}/start", response_model=ProposalOut)
def start_proposal(
    prop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    try:
        return transition_proposal(
            db=db,
            proposal=prop,
            new_status="IN_PROGRESS",
            actor_id=current_user.id,
            comment="Nhân viên bắt đầu liên hệ nhà cung cấp và nhập hàng"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{prop_id}/complete", response_model=ProposalOut)
def complete_proposal(
    prop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    try:
        return transition_proposal(
            db=db,
            proposal=prop,
            new_status="COMPLETED",
            actor_id=current_user.id,
            comment="Đã hoàn tất nhận hàng vào kho & cập nhật tồn kho tự động"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{prop_id}/cancel", response_model=ProposalOut)
def cancel_proposal(
    prop_id: int,
    payload: ProposalStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Proposal).filter(Proposal.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất")
    # Only creator or manager can cancel
    if current_user.role != "manager" and prop.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hủy đề xuất này")
    try:
        return transition_proposal(
            db=db,
            proposal=prop,
            new_status="CANCELLED",
            actor_id=current_user.id,
            comment=payload.comment or "Đã hủy đề xuất"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
