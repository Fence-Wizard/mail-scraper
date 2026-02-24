from datetime import datetime
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .db import db_session, ensure_schema
from .db_schema import (
    AppUser,
    DecisionScore,
    InvoiceMatch,
    OrderConfirmation,
    PurchaseOrder,
    RfqQuote,
    Task,
    TaskEvent,
    VendorKpi,
    VendorReference,
    WorkflowAction,
)

app = FastAPI(title="Procurement Webapp API", version="0.1.0")


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _require_role(role_required: str) -> Callable[[str | None], AppUser]:
    hierarchy = {"viewer": 0, "buyer": 1, "approver": 2, "admin": 3}

    def dependency(x_user_email: str | None = Header(default=None, alias="X-User-Email")) -> AppUser:
        if not x_user_email:
            raise HTTPException(status_code=401, detail="Missing X-User-Email header")
        with db_session() as session:
            user = session.execute(select(AppUser).where(AppUser.email == x_user_email)).scalar_one_or_none()
            if user is None or not user.is_active:
                raise HTTPException(status_code=403, detail="User not authorized")
            if hierarchy.get(user.role, -1) < hierarchy.get(role_required, 0):
                raise HTTPException(status_code=403, detail="Insufficient role")
            return user

    return dependency


class RfqCreateRequest(BaseModel):
    job_number: str | None = None
    vendor_reference_id: int | None = None
    quote_amount: float | None = None
    status: str = "requested"
    notes: str | None = None


class PoCreateRequest(BaseModel):
    po_number: str
    job_number: str | None = None
    vendor_reference_id: int | None = None
    total_amount: float | None = None
    status: str = "draft"
    source_task_id: int | None = None
    notes: str | None = None


class ApprovePoRequest(BaseModel):
    notes: str | None = None


class ConfirmOrderRequest(BaseModel):
    status: str = "confirmed"
    notes: str | None = None


class InvoiceResolveRequest(BaseModel):
    match_status: str = "matched"
    exception_reason: str | None = None


class DecisionProfileRequest(BaseModel):
    speed_weight: float = Field(default=1.0, ge=0.0)
    risk_weight: float = Field(default=1.0, ge=0.0)
    cash_weight: float = Field(default=1.0, ge=0.0)
    relationship_weight: float = Field(default=1.0, ge=0.0)
    rework_weight: float = Field(default=1.0, ge=0.0)


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(default="approve", pattern="^(approve|reject)$")
    notes: str | None = None


class AdvanceStageRequest(BaseModel):
    next_stage: str
    notes: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    ensure_schema()
    return {"status": "ok", "time": _now_iso()}


@app.get("/dashboard/summary")
def dashboard_summary(_user: AppUser = Depends(_require_role("viewer"))) -> dict[str, int | float]:
    with db_session() as session:
        open_tasks = session.execute(select(func.count()).select_from(Task).where(Task.status == "open")).scalar_one()
        financial_approvals_pending = session.execute(
            select(func.count()).select_from(Task).where(Task.status == "open", Task.human_required.is_(True))
        ).scalar_one()
        open_invoice_exceptions = session.execute(
            select(func.count()).select_from(InvoiceMatch).where(InvoiceMatch.match_status != "matched")
        ).scalar_one()
        pending_order_confirms = session.execute(
            select(func.count()).select_from(OrderConfirmation).where(OrderConfirmation.status != "confirmed")
        ).scalar_one()
        top_priority = session.execute(
            select(func.count()).select_from(Task).where(Task.status == "open", Task.priority == "high")
        ).scalar_one()
        spend = session.execute(select(func.coalesce(func.sum(PurchaseOrder.total_amount), 0.0))).scalar_one()
    return {
        "open_tasks": int(open_tasks),
        "financial_approvals_pending": int(financial_approvals_pending),
        "open_invoice_exceptions": int(open_invoice_exceptions),
        "pending_order_confirmations": int(pending_order_confirms),
        "open_high_priority_tasks": int(top_priority),
        "tracked_po_spend": float(spend or 0.0),
    }


@app.get("/vendors")
def list_vendors(limit: int = Query(default=100, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))):
    with db_session() as session:
        rows = session.execute(select(VendorReference).order_by(VendorReference.vendor_name.asc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "vendor_code": row.vendor_code,
            "vendor_name": row.vendor_name,
            "vendor_class": row.vendor_class,
            "vendor_status": row.vendor_status,
        }
        for row in rows
    ]


@app.get("/vendors/kpis")
def vendor_kpis(limit: int = Query(default=100, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))):
    with db_session() as session:
        rows = session.execute(
            select(VendorKpi).order_by(desc(VendorKpi.total_spend)).limit(limit)
        ).scalars().all()
    return [
        {
            "vendor_reference_id": row.vendor_reference_id,
            "period_start": row.period_start,
            "period_end": row.period_end,
            "on_time_rate": row.on_time_rate,
            "avg_cycle_days": row.avg_cycle_days,
            "exception_rate": row.exception_rate,
            "total_spend": row.total_spend,
        }
        for row in rows
    ]


@app.get("/tasks")
def list_tasks(
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    _user: AppUser = Depends(_require_role("viewer")),
):
    with db_session() as session:
        stmt = select(Task).order_by(Task.id.desc()).limit(limit)
        if status:
            stmt = stmt.where(Task.status == status)
        rows = session.execute(stmt).scalars().all()
    return [
        {
            "id": row.id,
            "task_type": row.task_type,
            "status": row.status,
            "priority": row.priority,
            "job_number": row.job_number,
            "workflow_spine": row.workflow_spine,
            "workflow_stage": row.workflow_stage,
            "human_required": row.human_required,
            "auto_allowed": row.auto_allowed,
            "blocked_reason": row.blocked_reason,
            "source_folder_path": row.source_folder_path,
            "source_message_id": row.source_message_id,
            "source_document_id": row.source_document_id,
            "details": row.details_json,
        }
        for row in rows
    ]


@app.get("/rfqs")
def list_rfqs(limit: int = Query(default=200, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))):
    with db_session() as session:
        rows = session.execute(select(RfqQuote).order_by(RfqQuote.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "job_number": row.job_number,
            "vendor_reference_id": row.vendor_reference_id,
            "status": row.status,
            "quote_amount": row.quote_amount,
            "request_date": row.request_date,
        }
        for row in rows
    ]


@app.post("/rfqs")
def create_rfq(payload: RfqCreateRequest, user: AppUser = Depends(_require_role("buyer"))):
    with db_session() as session:
        row = RfqQuote(
            job_number=payload.job_number,
            vendor_reference_id=payload.vendor_reference_id,
            requested_by_actor_id=None,
            status=payload.status,
            request_date=datetime.utcnow(),
            quote_amount=payload.quote_amount,
            currency="USD",
            notes=payload.notes,
            source_task_id=None,
        )
        session.add(row)
        session.flush()
        return {"id": row.id, "created_by": user.email}


@app.get("/purchase-orders")
def list_purchase_orders(
    limit: int = Query(default=200, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))
):
    with db_session() as session:
        rows = session.execute(select(PurchaseOrder).order_by(PurchaseOrder.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "po_number": row.po_number,
            "job_number": row.job_number,
            "status": row.status,
            "total_amount": row.total_amount,
            "approved_at": row.approved_at,
            "issued_at": row.issued_at,
        }
        for row in rows
    ]


@app.post("/purchase-orders")
def create_purchase_order(payload: PoCreateRequest, user: AppUser = Depends(_require_role("buyer"))):
    with db_session() as session:
        existing = session.execute(select(PurchaseOrder).where(PurchaseOrder.po_number == payload.po_number)).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="PO number already exists")
        row = PurchaseOrder(
            po_number=payload.po_number,
            job_number=payload.job_number,
            vendor_reference_id=payload.vendor_reference_id,
            created_by_user_id=user.id,
            approved_by_user_id=None,
            status=payload.status,
            total_amount=payload.total_amount,
            approved_at=None,
            issued_at=None,
            source_task_id=payload.source_task_id,
            notes=payload.notes,
        )
        session.add(row)
        session.flush()
        session.add(
            WorkflowAction(
                task_id=payload.source_task_id,
                action_type="po_created",
                action_mode="human",
                action_status="applied",
                actor_email=user.email,
                notes="PO created by buyer",
                payload_json={"po_id": row.id, "po_number": row.po_number},
            )
        )
        return {"id": row.id, "po_number": row.po_number}


@app.post("/purchase-orders/{po_id}/approve")
def approve_purchase_order(po_id: int, payload: ApprovePoRequest, user: AppUser = Depends(_require_role("approver"))):
    with db_session() as session:
        row = session.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="PO not found")
        row.status = "approved"
        row.approved_by_user_id = user.id
        row.approved_at = datetime.utcnow()
        row.issued_at = row.issued_at or datetime.utcnow()
        if payload.notes:
            row.notes = payload.notes
        if row.source_task_id is not None:
            task = session.execute(select(Task).where(Task.id == row.source_task_id)).scalar_one_or_none()
            if task is not None:
                task.human_required = False
                task.blocked_reason = None
                task.status = "completed"
                task.completed_at = datetime.utcnow()
                task.workflow_stage = "invoice_match_completed"
                session.add(
                    TaskEvent(
                        task_id=task.id,
                        event_type="approval_completed",
                        message_id=task.source_message_id,
                        document_id=task.source_document_id,
                        notes="Financial approval completed by approver.",
                        payload_json={"approved_by": user.email, "po_id": row.id},
                    )
                )
                session.add(
                    WorkflowAction(
                        task_id=task.id,
                        action_type="financial_transition_approved",
                        action_mode="human",
                        action_status="applied",
                        actor_email=user.email,
                        notes=payload.notes or "PO approval applied",
                        payload_json={"po_id": row.id},
                    )
                )
        return {"id": row.id, "status": row.status, "approved_by": user.email}


@app.get("/order-confirmations")
def list_order_confirmations(
    limit: int = Query(default=200, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))
):
    with db_session() as session:
        rows = session.execute(select(OrderConfirmation).order_by(OrderConfirmation.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "purchase_order_id": row.purchase_order_id,
            "status": row.status,
            "confirmed_at": row.confirmed_at,
            "source_document_id": row.source_document_id,
        }
        for row in rows
    ]


@app.post("/order-confirmations/{confirmation_id}")
def update_order_confirmation(
    confirmation_id: int, payload: ConfirmOrderRequest, _user: AppUser = Depends(_require_role("buyer"))
):
    with db_session() as session:
        row = session.execute(select(OrderConfirmation).where(OrderConfirmation.id == confirmation_id)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Order confirmation not found")
        row.status = payload.status
        row.confirmed_at = datetime.utcnow() if payload.status == "confirmed" else None
        if payload.notes:
            row.notes = payload.notes
        return {"id": row.id, "status": row.status}


@app.get("/invoice-matches")
def list_invoice_matches(
    status: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    _user: AppUser = Depends(_require_role("viewer")),
):
    with db_session() as session:
        stmt = select(InvoiceMatch).order_by(InvoiceMatch.id.desc()).limit(limit)
        if status:
            stmt = stmt.where(InvoiceMatch.match_status == status)
        rows = session.execute(stmt).scalars().all()
    return [
        {
            "id": row.id,
            "document_id": row.document_id,
            "purchase_order_id": row.purchase_order_id,
            "match_status": row.match_status,
            "variance_amount": row.variance_amount,
            "exception_reason": row.exception_reason,
        }
        for row in rows
    ]


@app.post("/invoice-matches/{match_id}/resolve")
def resolve_invoice_match(match_id: int, payload: InvoiceResolveRequest, _user: AppUser = Depends(_require_role("approver"))):
    with db_session() as session:
        row = session.execute(select(InvoiceMatch).where(InvoiceMatch.id == match_id)).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Invoice match row not found")
        row.match_status = payload.match_status
        row.exception_reason = payload.exception_reason
        row.resolved_at = datetime.utcnow() if payload.match_status == "matched" else None
        return {"id": row.id, "match_status": row.match_status}


@app.get("/approvals/financial")
def list_financial_approvals(
    limit: int = Query(default=200, ge=1, le=1000),
    _user: AppUser = Depends(_require_role("approver")),
):
    with db_session() as session:
        rows = session.execute(
            select(Task)
            .where(Task.status == "open", Task.human_required.is_(True))
            .order_by(Task.priority.desc(), Task.id.desc())
            .limit(limit)
        ).scalars().all()
    return [
        {
            "task_id": row.id,
            "workflow_stage": row.workflow_stage,
            "job_number": row.job_number,
            "priority": row.priority,
            "blocked_reason": row.blocked_reason,
            "details": row.details_json,
            "due_at": row.due_at,
        }
        for row in rows
    ]


@app.post("/approvals/financial/{task_id}")
def decide_financial_approval(
    task_id: int,
    payload: ApprovalDecisionRequest,
    user: AppUser = Depends(_require_role("approver")),
):
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if not task.human_required:
            raise HTTPException(status_code=409, detail="Task is not in human approval state")

        if payload.decision == "approve":
            task.human_required = False
            task.blocked_reason = None
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.workflow_stage = "invoice_match_completed"
            action_type = "financial_transition_approved"
            notes = payload.notes or "Approved in financial approval queue"
        else:
            task.status = "open"
            task.human_required = True
            task.blocked_reason = payload.notes or "Rejected by approver; needs rework"
            action_type = "financial_transition_rejected"
            notes = task.blocked_reason

        task.last_event_at = datetime.utcnow()
        session.add(
            TaskEvent(
                task_id=task.id,
                event_type=action_type,
                message_id=task.source_message_id,
                document_id=task.source_document_id,
                notes=notes,
                payload_json={"actor": user.email, "decision": payload.decision},
            )
        )
        session.add(
            WorkflowAction(
                task_id=task.id,
                action_type=action_type,
                action_mode="human",
                action_status="applied",
                actor_email=user.email,
                notes=notes,
                payload_json={"decision": payload.decision},
            )
        )
        return {"task_id": task.id, "decision": payload.decision, "status": task.status}


@app.get("/workflow/lanes")
def workflow_lanes(
    limit_per_lane: int = Query(default=50, ge=1, le=300),
    _user: AppUser = Depends(_require_role("viewer")),
):
    lane_order = [
        "job_setup",
        "budget_review",
        "task_assignment",
        "material_check",
        "pricing_validation",
        "vendor_coordination",
        "order_placement",
        "order_confirmation",
        "yard_pull",
        "material_receiving",
        "completion_check",
        "completed",
    ]
    with db_session() as session:
        tasks = session.execute(select(Task).order_by(Task.id.desc())).scalars().all()

    lanes: dict[str, list[dict]] = {lane: [] for lane in lane_order}
    for task in tasks:
        lane = task.workflow_stage or "job_setup"
        if lane not in lanes:
            lanes[lane] = []
        if len(lanes[lane]) >= limit_per_lane:
            continue
        lanes[lane].append(
            {
                "task_id": task.id,
                "job_number": task.job_number,
                "status": task.status,
                "priority": task.priority,
                "human_required": task.human_required,
                "auto_allowed": task.auto_allowed,
                "blocked_reason": task.blocked_reason,
                "due_at": task.due_at,
                "details": task.details_json,
            }
        )

    return {
        "lane_order": lane_order,
        "lanes": lanes,
    }


@app.post("/workflow/advance/{task_id}")
def advance_workflow_stage(
    task_id: int,
    payload: AdvanceStageRequest,
    user: AppUser = Depends(_require_role("buyer")),
):
    valid_stages = {
        "job_setup", "budget_review", "task_assignment", "material_check",
        "pricing_validation", "vendor_coordination", "order_placement",
        "order_confirmation", "yard_pull", "material_receiving",
        "completion_check", "completed",
    }
    if payload.next_stage not in valid_stages:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {payload.next_stage}")
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        old_stage = task.workflow_stage
        task.workflow_stage = payload.next_stage
        task.last_event_at = datetime.utcnow()
        if payload.next_stage == "completed":
            task.status = "completed"
            task.completed_at = datetime.utcnow()
        financial_stages = {"budget_review", "pricing_validation", "order_placement"}
        task.human_required = payload.next_stage in financial_stages and (
            (task.details_json or {}).get("total") or 0
        ) >= 25000
        task.auto_allowed = payload.next_stage not in financial_stages
        task.blocked_reason = None
        session.add(
            TaskEvent(
                task_id=task.id,
                event_type="stage_advanced",
                message_id=task.source_message_id,
                document_id=task.source_document_id,
                notes=payload.notes or f"Advanced from {old_stage} to {payload.next_stage}",
                payload_json={"from": old_stage, "to": payload.next_stage},
            )
        )
        session.add(
            WorkflowAction(
                task_id=task.id,
                action_type="stage_advanced",
                action_mode="human",
                action_status="applied",
                actor_email=user.email,
                notes=payload.notes or f"{old_stage} → {payload.next_stage}",
                payload_json={"from": old_stage, "to": payload.next_stage},
            )
        )
        return {"task_id": task.id, "old_stage": old_stage, "new_stage": payload.next_stage}


@app.get("/workflow/actions/recent")
def recent_workflow_actions(
    limit: int = Query(default=100, ge=1, le=500),
    _user: AppUser = Depends(_require_role("viewer")),
):
    with db_session() as session:
        rows = session.execute(select(WorkflowAction).order_by(WorkflowAction.id.desc()).limit(limit)).scalars().all()
    return [
        {
            "id": row.id,
            "task_id": row.task_id,
            "action_type": row.action_type,
            "action_mode": row.action_mode,
            "action_status": row.action_status,
            "actor_email": row.actor_email,
            "notes": row.notes,
            "created_at": row.created_at,
            "payload": row.payload_json,
        }
        for row in rows
    ]


@app.get("/decisions/top")
def top_decisions(limit: int = Query(default=100, ge=1, le=1000), _user: AppUser = Depends(_require_role("viewer"))):
    with db_session() as session:
        rows = session.execute(
            select(DecisionScore).order_by(DecisionScore.score_total.desc()).limit(limit)
        ).scalars().all()
    return [
        {
            "task_id": row.task_id,
            "action_label": row.action_label,
            "score_total": row.score_total,
            "score_components": {
                "speed": row.score_speed,
                "risk": row.score_risk,
                "cash": row.score_cash,
                "relationship": row.score_relationship,
                "rework": row.score_rework,
            },
        }
        for row in rows
    ]


@app.post("/decisions/rescore")
def rescore_decisions(payload: DecisionProfileRequest, _user: AppUser = Depends(_require_role("approver"))):
    from .operations import run_score_decisions

    result = run_score_decisions(
        speed_weight=payload.speed_weight,
        risk_weight=payload.risk_weight,
        cash_weight=payload.cash_weight,
        relationship_weight=payload.relationship_weight,
        rework_weight=payload.rework_weight,
    )
    return {"rescored": result["tasks_scored"]}
