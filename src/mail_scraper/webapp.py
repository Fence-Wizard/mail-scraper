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

app = FastAPI(title="Procurement Webapp API", version="2.0.0")


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


def _task_dict(row: Task) -> dict:
    """Serialize a Task row to a dict for API responses."""
    return {
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
        "assigned_purchaser_email": row.assigned_purchaser_email,
        "assigned_by_email": row.assigned_by_email,
        "material_in_stock": row.material_in_stock,
        "can_pull_extra": row.can_pull_extra,
        "po_provided": row.po_provided,
        "prices_valid": row.prices_valid,
        "all_material_present": row.all_material_present,
        "vendor_coord_price": row.vendor_coord_price,
        "vendor_coord_delivery_time": row.vendor_coord_delivery_time,
        "vendor_coord_delivery_location": row.vendor_coord_delivery_location,
        "expected_delivery_date": row.expected_delivery_date.isoformat() if row.expected_delivery_date else None,
        "backorder_notes": row.backorder_notes,
        "decision_path": row.decision_path,
        "details": row.details_json,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _add_event(session: Session, task: Task, event_type: str, notes: str, payload: dict | None = None) -> None:
    session.add(TaskEvent(
        task_id=task.id,
        event_type=event_type,
        message_id=task.source_message_id,
        document_id=task.source_document_id,
        notes=notes,
        payload_json=payload or {},
    ))


def _add_action(session: Session, task: Task, action_type: str, actor_email: str, notes: str, payload: dict | None = None) -> None:
    session.add(WorkflowAction(
        task_id=task.id,
        action_type=action_type,
        action_mode="human",
        action_status="applied",
        actor_email=actor_email,
        notes=notes,
        payload_json=payload or {},
    ))


def _append_decision(task: Task, decision: str) -> None:
    path = list(task.decision_path or [])
    path.append({"decision": decision, "at": _now_iso(), "stage": task.workflow_stage})
    task.decision_path = path


# ---- Request models ----

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


class IntakeSubmission(BaseModel):
    job_number: str | None = None
    location: str | None = None
    vendor: str | None = None
    budget_amount: float | None = None
    po_number: str | None = None
    submitted_by: str | None = None
    subject: str | None = None
    notes: str | None = None
    priority: str = Field(default="normal", pattern="^(normal|high)$")
    source: str = Field(default="manual", pattern="^(manual|email_forward|email_cc)$")


class BudgetReviewRequest(BaseModel):
    budget_good: bool
    quality_errors: str | None = None
    notes: str | None = None


class AssignPurchaserRequest(BaseModel):
    purchaser_email: str
    notes: str | None = None


class MaterialCheckRequest(BaseModel):
    material_in_stock: bool
    can_pull_extra: bool = False
    notes: str | None = None


class PricingCheckRequest(BaseModel):
    po_provided: bool
    prices_valid: bool | None = None
    notes: str | None = None


class VendorCoordinationRequest(BaseModel):
    price: str | None = None
    delivery_time: str | None = None
    delivery_location: str | None = None
    notes: str | None = None


class CompletionCheckRequest(BaseModel):
    all_material_present: bool
    backorder_notes: str | None = None
    expected_delivery_date: str | None = None


# ---- Intake ----


@app.post("/intake")
def submit_intake(
    payload: IntakeSubmission,
    user: AppUser = Depends(_require_role("buyer")),
):
    """Create a new job from an intake submission (manual form or future email hook)."""
    with db_session() as session:
        task = Task(
            task_type="job_setup",
            status="open",
            priority=payload.priority,
            job_number=payload.job_number,
            workflow_spine="intake",
            workflow_stage="job_setup",
            human_required=False,
            auto_allowed=True,
            source_folder_path=payload.location,
            last_event_at=datetime.utcnow(),
            po_provided=bool(payload.po_number),
            decision_path=[],
            details_json={
                "vendor": payload.vendor,
                "po_number": payload.po_number,
                "total": payload.budget_amount,
                "location": payload.location,
                "subject": payload.subject,
                "notes": payload.notes,
                "submitted_by": payload.submitted_by or user.email,
                "source": payload.source,
            },
        )
        session.add(task)
        session.flush()
        task_id = task.id
        _add_event(session, task, "intake_submitted",
                    f"Submitted via {payload.source} by {payload.submitted_by or user.email}",
                    {"job_number": payload.job_number, "vendor": payload.vendor, "budget_amount": payload.budget_amount, "source": payload.source})
        _add_action(session, task, "intake_submitted", payload.submitted_by or user.email,
                     payload.subject or f"Job {payload.job_number or 'N/A'} intake",
                     {"job_number": payload.job_number, "vendor": payload.vendor, "budget_amount": payload.budget_amount})

    return {"task_id": task_id, "status": "created", "workflow_stage": "job_setup"}


@app.get("/intake/recent")
def recent_intakes(
    limit: int = Query(default=50, ge=1, le=500),
    _user: AppUser = Depends(_require_role("viewer")),
):
    with db_session() as session:
        rows = session.execute(
            select(Task)
            .where(Task.workflow_spine == "intake")
            .order_by(Task.id.desc())
            .limit(limit)
        ).scalars().all()
    return [
        {
            "id": r.id,
            "job_number": r.job_number,
            "status": r.status,
            "priority": r.priority,
            "workflow_stage": r.workflow_stage,
            "human_required": r.human_required,
            "assigned_purchaser_email": r.assigned_purchaser_email,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "details": r.details_json or {},
        }
        for r in rows
    ]


# ---- Decision-Gate Workflow Endpoints ----
# These map directly to the diamond gates in the workflow diagram.


@app.post("/workflow/budget-review/{task_id}")
def budget_review(
    task_id: int,
    payload: BudgetReviewRequest,
    user: AppUser = Depends(_require_role("approver")),
):
    """Decision gate: Budget Quality Check.
    If budget_good=true, advance to task_assignment.
    If budget_good=false, loop back to job_setup for PM revision.
    """
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage not in ("job_setup", "budget_review"):
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not budget_review")

        old_stage = task.workflow_stage
        task.last_event_at = datetime.utcnow()

        if payload.budget_good:
            task.workflow_stage = "task_assignment"
            task.human_required = True
            task.blocked_reason = "Needs purchaser assignment by Project Manager"
            _append_decision(task, "budget_approved")
            notes = payload.notes or "Budget approved - ready for purchaser assignment"
        else:
            task.workflow_stage = "job_setup"
            task.human_required = True
            task.blocked_reason = f"Quality errors: {payload.quality_errors or 'See notes'}"
            _append_decision(task, "budget_rejected")
            notes = f"Budget rejected: {payload.quality_errors or payload.notes or 'Quality errors found'}"

        _add_event(session, task, "budget_review", notes, {"budget_good": payload.budget_good, "from": old_stage, "to": task.workflow_stage})
        _add_action(session, task, "budget_review", user.email, notes, {"budget_good": payload.budget_good})
        return {"task_id": task.id, "new_stage": task.workflow_stage, "budget_good": payload.budget_good}


@app.post("/workflow/assign-purchaser/{task_id}")
def assign_purchaser(
    task_id: int,
    payload: AssignPurchaserRequest,
    user: AppUser = Depends(_require_role("approver")),
):
    """Task assigned to Purchaser by Project Manager assignments."""
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "task_assignment":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not task_assignment")

        task.assigned_purchaser_email = payload.purchaser_email
        task.assigned_by_email = user.email
        task.workflow_stage = "material_check"
        task.human_required = True
        task.blocked_reason = "Purchaser must check material availability"
        task.last_event_at = datetime.utcnow()
        _append_decision(task, f"assigned:{payload.purchaser_email}")

        notes = payload.notes or f"Assigned to {payload.purchaser_email}"
        _add_event(session, task, "purchaser_assigned", notes, {"purchaser": payload.purchaser_email, "assigned_by": user.email})
        _add_action(session, task, "purchaser_assigned", user.email, notes, {"purchaser": payload.purchaser_email})
        return {"task_id": task.id, "new_stage": "material_check", "assigned_to": payload.purchaser_email}


@app.post("/workflow/material-check/{task_id}")
def material_check(
    task_id: int,
    payload: MaterialCheckRequest,
    user: AppUser = Depends(_require_role("buyer")),
):
    """Decision gate: Is Material in Stock? + Can we pull from extra materials?

    Branching logic from the diagram:
    - In stock + can pull extra -> Reserve materials -> yard_pull
    - In stock + cannot pull extra -> yard_pull (generate yard pull)
    - Not in stock + can pull extra -> Reserve materials -> yard_pull
    - Not in stock + cannot pull extra -> Check if PO provided -> pricing_validation
    """
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "material_check":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not material_check")

        task.material_in_stock = payload.material_in_stock
        task.can_pull_extra = payload.can_pull_extra
        task.last_event_at = datetime.utcnow()

        if payload.material_in_stock or payload.can_pull_extra:
            # Material available path: Reserve & generate yard pull
            task.workflow_stage = "yard_pull"
            task.human_required = False
            task.auto_allowed = True
            task.blocked_reason = None
            decision = "material_available"
            notes = payload.notes or "Material available - generating yard pull"
            if payload.can_pull_extra:
                notes = payload.notes or "Pulling from extra materials - reserve & generate yard pull"
                decision = "pull_extra_materials"
        else:
            # Not in stock, can't pull extra -> procurement path
            task.workflow_stage = "pricing_validation"
            task.human_required = True
            task.blocked_reason = "Material not available - check if PO was provided"
            decision = "material_not_available"
            notes = payload.notes or "Material not in stock - proceeding to procurement"

        _append_decision(task, decision)
        _add_event(session, task, "material_check", notes,
                   {"in_stock": payload.material_in_stock, "can_pull_extra": payload.can_pull_extra, "to": task.workflow_stage})
        _add_action(session, task, "material_check", user.email, notes,
                    {"in_stock": payload.material_in_stock, "can_pull_extra": payload.can_pull_extra})
        return {"task_id": task.id, "new_stage": task.workflow_stage, "in_stock": payload.material_in_stock, "can_pull_extra": payload.can_pull_extra}


@app.post("/workflow/pricing-check/{task_id}")
def pricing_check(
    task_id: int,
    payload: PricingCheckRequest,
    user: AppUser = Depends(_require_role("buyer")),
):
    """Decision gate: Was PO provided? + Are prices still valid?

    Branching logic:
    - PO provided + prices valid -> order_placement (Order Material)
    - PO provided + prices NOT valid -> vendor_coordination
    - No PO provided -> vendor_coordination
    """
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "pricing_validation":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not pricing_validation")

        task.po_provided = payload.po_provided
        task.prices_valid = payload.prices_valid
        task.last_event_at = datetime.utcnow()

        if payload.po_provided and payload.prices_valid:
            task.workflow_stage = "order_placement"
            task.human_required = True
            task.blocked_reason = "Ready to place order"
            decision = "po_valid"
            notes = payload.notes or "PO provided with valid pricing - ready to order"
        else:
            task.workflow_stage = "vendor_coordination"
            task.human_required = True
            if not payload.po_provided:
                task.blocked_reason = "No PO - vendor coordination needed for pricing"
                decision = "no_po"
                notes = payload.notes or "No PO provided - needs vendor coordination"
            else:
                task.blocked_reason = "Prices outdated - vendor coordination needed"
                decision = "prices_invalid"
                notes = payload.notes or "PO prices no longer valid - needs vendor coordination"

        _append_decision(task, decision)
        _add_event(session, task, "pricing_check", notes,
                   {"po_provided": payload.po_provided, "prices_valid": payload.prices_valid, "to": task.workflow_stage})
        _add_action(session, task, "pricing_check", user.email, notes,
                    {"po_provided": payload.po_provided, "prices_valid": payload.prices_valid})
        return {"task_id": task.id, "new_stage": task.workflow_stage, "po_provided": payload.po_provided, "prices_valid": payload.prices_valid}


@app.post("/workflow/vendor-coordination/{task_id}")
def vendor_coordination(
    task_id: int,
    payload: VendorCoordinationRequest,
    user: AppUser = Depends(_require_role("buyer")),
):
    """Vendor Coordination: Price, Delivery Time, Delivery Location.
    After coordination is complete, advance to order_placement.
    """
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "vendor_coordination":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not vendor_coordination")

        task.vendor_coord_price = payload.price
        task.vendor_coord_delivery_time = payload.delivery_time
        task.vendor_coord_delivery_location = payload.delivery_location
        task.workflow_stage = "order_placement"
        task.human_required = True
        task.blocked_reason = "Vendor coordination complete - ready to place order"
        task.last_event_at = datetime.utcnow()
        _append_decision(task, "vendor_coordination_complete")

        notes = payload.notes or f"Coordinated: price={payload.price}, delivery={payload.delivery_time}, location={payload.delivery_location}"
        _add_event(session, task, "vendor_coordination", notes,
                   {"price": payload.price, "delivery_time": payload.delivery_time, "delivery_location": payload.delivery_location})
        _add_action(session, task, "vendor_coordination", user.email, notes,
                    {"price": payload.price, "delivery_time": payload.delivery_time, "delivery_location": payload.delivery_location})
        return {"task_id": task.id, "new_stage": "order_placement"}


@app.post("/workflow/place-order/{task_id}")
def place_order(
    task_id: int,
    user: AppUser = Depends(_require_role("buyer")),
    notes: str | None = Query(default=None),
):
    """Order Material - advance to order_confirmation to await vendor confirmation and lead times."""
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "order_placement":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not order_placement")

        task.workflow_stage = "order_confirmation"
        task.human_required = True
        task.blocked_reason = "Awaiting order confirmation and lead times from vendor"
        task.last_event_at = datetime.utcnow()
        _append_decision(task, "order_placed")

        msg = notes or "Order placed - awaiting vendor confirmation"
        _add_event(session, task, "order_placed", msg, {"to": "order_confirmation"})
        _add_action(session, task, "order_placed", user.email, msg, {})
        return {"task_id": task.id, "new_stage": "order_confirmation"}


@app.post("/workflow/confirm-order/{task_id}")
def confirm_order(
    task_id: int,
    user: AppUser = Depends(_require_role("buyer")),
    notes: str | None = Query(default=None),
    expected_delivery_date: str | None = Query(default=None),
):
    """Order Confirmation received with lead times -> Generate Yard Pull -> Material Arrives."""
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "order_confirmation":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not order_confirmation")

        if expected_delivery_date:
            try:
                task.expected_delivery_date = datetime.fromisoformat(expected_delivery_date)
            except ValueError:
                pass
        task.workflow_stage = "yard_pull"
        task.human_required = False
        task.auto_allowed = True
        task.blocked_reason = None
        task.last_event_at = datetime.utcnow()
        _append_decision(task, "order_confirmed")

        msg = notes or "Order confirmed - generating yard pull"
        _add_event(session, task, "order_confirmed", msg, {"expected_delivery": expected_delivery_date})
        _add_action(session, task, "order_confirmed", user.email, msg, {"expected_delivery": expected_delivery_date})
        return {"task_id": task.id, "new_stage": "yard_pull"}


@app.post("/workflow/material-arrives/{task_id}")
def material_arrives(
    task_id: int,
    user: AppUser = Depends(_require_role("buyer")),
    notes: str | None = Query(default=None),
):
    """Material arrives at yard -> advance to completion_check."""
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage not in ("yard_pull", "material_receiving"):
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, expected yard_pull or material_receiving")

        task.workflow_stage = "completion_check"
        task.human_required = True
        task.blocked_reason = "Verify all material is present"
        task.last_event_at = datetime.utcnow()
        _append_decision(task, "material_arrived")

        msg = notes or "Material arrived - checking completeness"
        _add_event(session, task, "material_arrived", msg, {"to": "completion_check"})
        _add_action(session, task, "material_arrived", user.email, msg, {})
        return {"task_id": task.id, "new_stage": "completion_check"}


@app.post("/workflow/completion-check/{task_id}")
def completion_check(
    task_id: int,
    payload: CompletionCheckRequest,
    user: AppUser = Depends(_require_role("buyer")),
):
    """Decision gate: All Material Present?
    - Yes -> completed (Job Scheduled)
    - No -> back to vendor_coordination for back-ordered materials
    """
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if task.workflow_stage != "completion_check":
            raise HTTPException(status_code=409, detail=f"Task is at {task.workflow_stage}, not completion_check")

        task.all_material_present = payload.all_material_present
        task.last_event_at = datetime.utcnow()

        if payload.all_material_present:
            task.workflow_stage = "completed"
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.human_required = False
            task.blocked_reason = None
            _append_decision(task, "all_material_present")
            notes = "All material present - job scheduled"
        else:
            task.workflow_stage = "vendor_coordination"
            task.human_required = True
            task.blocked_reason = "Back-ordered materials - confirm vendor arrival dates"
            task.backorder_notes = payload.backorder_notes
            if payload.expected_delivery_date:
                try:
                    task.expected_delivery_date = datetime.fromisoformat(payload.expected_delivery_date)
                except ValueError:
                    pass
            _append_decision(task, "backorder_loop")
            notes = f"Missing material - back to vendor coordination. {payload.backorder_notes or ''}"

        _add_event(session, task, "completion_check", notes,
                   {"all_present": payload.all_material_present, "to": task.workflow_stage})
        _add_action(session, task, "completion_check", user.email, notes,
                    {"all_present": payload.all_material_present, "backorder_notes": payload.backorder_notes})
        return {"task_id": task.id, "new_stage": task.workflow_stage, "all_material_present": payload.all_material_present}


# ---- Task detail with timeline ----


@app.get("/tasks/{task_id}")
def get_task_detail(
    task_id: int,
    _user: AppUser = Depends(_require_role("viewer")),
):
    with db_session() as session:
        task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        events = session.execute(
            select(TaskEvent).where(TaskEvent.task_id == task_id).order_by(TaskEvent.event_at.asc())
        ).scalars().all()
        actions = session.execute(
            select(WorkflowAction).where(WorkflowAction.task_id == task_id).order_by(WorkflowAction.id.asc())
        ).scalars().all()
    return {
        "task": _task_dict(task),
        "events": [
            {"id": e.id, "event_type": e.event_type, "notes": e.notes, "at": e.event_at.isoformat() if e.event_at else None, "payload": e.payload_json}
            for e in events
        ],
        "actions": [
            {"id": a.id, "action_type": a.action_type, "actor_email": a.actor_email, "notes": a.notes, "at": a.created_at.isoformat() if a.created_at else None}
            for a in actions
        ],
    }


# ---- Original endpoints (preserved) ----


@app.get("/health")
def health() -> dict[str, str]:
    ensure_schema()
    return {"status": "ok", "time": _now_iso()}


@app.get("/dashboard/summary")
def dashboard_summary(_user: AppUser = Depends(_require_role("viewer"))) -> dict:
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
        # Per-stage counts for the overview
        awaiting_budget = session.execute(
            select(func.count()).select_from(Task).where(Task.status == "open", Task.workflow_stage.in_(("job_setup", "budget_review")))
        ).scalar_one()
        awaiting_assignment = session.execute(
            select(func.count()).select_from(Task).where(Task.status == "open", Task.workflow_stage == "task_assignment")
        ).scalar_one()
        in_procurement = session.execute(
            select(func.count()).select_from(Task).where(
                Task.status == "open",
                Task.workflow_stage.in_(("pricing_validation", "vendor_coordination", "order_placement", "order_confirmation")),
            )
        ).scalar_one()
        in_fulfillment = session.execute(
            select(func.count()).select_from(Task).where(
                Task.status == "open",
                Task.workflow_stage.in_(("material_check", "yard_pull", "material_receiving", "completion_check")),
            )
        ).scalar_one()
    return {
        "open_tasks": int(open_tasks),
        "financial_approvals_pending": int(financial_approvals_pending),
        "open_invoice_exceptions": int(open_invoice_exceptions),
        "pending_order_confirmations": int(pending_order_confirms),
        "open_high_priority_tasks": int(top_priority),
        "tracked_po_spend": float(spend or 0.0),
        "awaiting_budget_review": int(awaiting_budget),
        "awaiting_assignment": int(awaiting_assignment),
        "in_procurement": int(in_procurement),
        "in_fulfillment": int(in_fulfillment),
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
    return [_task_dict(row) for row in rows]


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
                task.workflow_stage = "completed"
                _add_event(session, task, "approval_completed", "Financial approval completed by approver.",
                           {"approved_by": user.email, "po_id": row.id})
                _add_action(session, task, "financial_transition_approved", user.email,
                            payload.notes or "PO approval applied", {"po_id": row.id})
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
            task.workflow_stage = "completed"
            action_type = "financial_transition_approved"
            notes = payload.notes or "Approved in financial approval queue"
        else:
            task.status = "open"
            task.human_required = True
            task.blocked_reason = payload.notes or "Rejected by approver; needs rework"
            action_type = "financial_transition_rejected"
            notes = task.blocked_reason

        task.last_event_at = datetime.utcnow()
        _add_event(session, task, action_type, notes, {"actor": user.email, "decision": payload.decision})
        _add_action(session, task, action_type, user.email, notes, {"decision": payload.decision})
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
        lanes[lane].append(_task_dict(task))

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
        _add_event(session, task, "stage_advanced",
                   payload.notes or f"Advanced from {old_stage} to {payload.next_stage}",
                   {"from": old_stage, "to": payload.next_stage})
        _add_action(session, task, "stage_advanced", user.email,
                    payload.notes or f"{old_stage} \u2192 {payload.next_stage}",
                    {"from": old_stage, "to": payload.next_stage})
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
