from datetime import datetime
from sqlalchemy.orm import Session
from app.models.proposal import Proposal, ProposalLog
from app.models.import_order import ImportOrder, ImportItem
from app.models.product import Product

VALID_TRANSITIONS = {
    "PENDING": ["APPROVED", "REJECTED", "CANCELLED"],
    "APPROVED": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["COMPLETED", "CANCELLED"],
    "REJECTED": [],
    "COMPLETED": [],
    "CANCELLED": [],
}

def transition_proposal(
    db: Session,
    proposal: Proposal,
    new_status: str,
    actor_id: int,
    comment: str = ""
) -> Proposal:
    allowed = VALID_TRANSITIONS.get(proposal.status, [])
    if new_status not in allowed:
        raise ValueError(f"Không thể chuyển trạng thái từ '{proposal.status}' sang '{new_status}'")

    proposal.status = new_status

    if new_status in ("APPROVED", "REJECTED"):
        proposal.reviewed_by = actor_id
        proposal.reviewed_at = datetime.utcnow()
        proposal.review_comment = comment

    # Ghi log lịch sử workflow
    log = ProposalLog(
        proposal_id=proposal.id,
        action=new_status,
        actor_id=actor_id,
        comment=comment,
        created_at=datetime.utcnow()
    )
    db.add(log)

    # Nếu hoàn thành nhập hàng -> tự động tạo phiếu nhập kho & cập nhật tồn
    if new_status == "COMPLETED":
        # Tìm nhà cung cấp từ sản phẩm đầu tiên hoặc None
        first_product = None
        if proposal.items:
            first_product = db.query(Product).filter(Product.id == proposal.items[0].product_id).first()
        supplier_id = first_product.supplier_id if first_product else None

        # Sinh mã phiếu nhập
        last_import = db.query(ImportOrder).order_by(ImportOrder.id.desc()).first()
        next_id = (last_import.id + 1) if last_import else 1
        import_code = f"PN{next_id:04d}"

        total_amount = 0.0
        import_order = ImportOrder(
            code=import_code,
            supplier_id=supplier_id,
            created_by=actor_id,
            created_at=datetime.utcnow(),
            notes=f"Nhập hàng tự động theo đề xuất đã duyệt: {proposal.code}",
            proposal_id=proposal.id,
            total_amount=0.0
        )
        db.add(import_order)
        db.flush()

        for item in proposal.items:
            prod = db.query(Product).filter(Product.id == item.product_id).first()
            unit_price = prod.price if prod else 0.0
            item_total = item.suggested_quantity * unit_price
            total_amount += item_total

            import_item = ImportItem(
                order_id=import_order.id,
                product_id=item.product_id,
                quantity=item.suggested_quantity,
                unit_price=unit_price
            )
            db.add(import_item)

            # Cập nhật tăng số lượng tồn kho
            if prod:
                prod.current_stock += item.suggested_quantity

        import_order.total_amount = total_amount

    db.commit()
    db.refresh(proposal)
    return proposal
