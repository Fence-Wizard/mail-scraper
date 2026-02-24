from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_key: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    root_folder_name: Mapped[str] = mapped_column(String(200), default="msgfolderroot")
    include_filters: Mapped[list[str]] = mapped_column(JSON, default=list)
    exclude_filters: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("mailbox_id", "graph_folder_id", name="uq_folder_mailbox_graph"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int] = mapped_column(ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True)
    graph_folder_id: Mapped[str] = mapped_column(String(256), index=True)
    parent_graph_folder_id: Mapped[str | None] = mapped_column(String(256))
    display_name: Mapped[str] = mapped_column(String(512))
    path: Mapped[str] = mapped_column(Text)
    total_item_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("mailbox_id", "graph_message_id", name="uq_message_mailbox_graph"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int] = mapped_column(ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True)
    graph_message_id: Mapped[str] = mapped_column(String(256), index=True)
    graph_folder_id: Mapped[str | None] = mapped_column(String(256), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(256), index=True)
    source_sender: Mapped[str | None] = mapped_column(String(320), index=True)
    source_subject: Mapped[str | None] = mapped_column(Text)
    source_received_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    body_preview: Mapped[str | None] = mapped_column(Text)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_json: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (UniqueConstraint("mailbox_id", "graph_attachment_id", name="uq_attachment_mailbox_graph"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int] = mapped_column(ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    graph_attachment_id: Mapped[str] = mapped_column(String(256), index=True)
    graph_message_id: Mapped[str] = mapped_column(String(256), index=True)
    name: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[str | None] = mapped_column(String(200))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    file_path: Mapped[str | None] = mapped_column(Text)
    download_status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    file_path: Mapped[str | None] = mapped_column(Text, unique=True)
    vendor: Mapped[str | None] = mapped_column(String(200), index=True)
    vendor_canonical: Mapped[str | None] = mapped_column(String(200), index=True)
    po_number: Mapped[str | None] = mapped_column(String(100), index=True)
    job_number: Mapped[str | None] = mapped_column(String(100), index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), index=True)
    invoice_date: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    subtotal: Mapped[float | None] = mapped_column(Float)
    tax: Mapped[float | None] = mapped_column(Float)
    total: Mapped[float | None] = mapped_column(Float, index=True)
    source_sender: Mapped[str | None] = mapped_column(String(320))
    source_received_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    source_subject: Mapped[str | None] = mapped_column(Text)
    extract_notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VendorReference(Base):
    __tablename__ = "vendor_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    vendor_name: Mapped[str] = mapped_column(String(300), index=True)
    vendor_name_canonical: Mapped[str] = mapped_column(String(300), index=True)
    vendor_class: Mapped[str | None] = mapped_column(String(100), index=True)
    vendor_status: Mapped[str | None] = mapped_column(String(100), index=True)
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(200))
    state: Mapped[str | None] = mapped_column(String(100))
    currency_id: Mapped[str | None] = mapped_column(String(50))
    terms: Mapped[str | None] = mapped_column(String(100))
    default_contact: Mapped[str | None] = mapped_column(String(100))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Actor(Base):
    __tablename__ = "actors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_key: Mapped[str] = mapped_column(String(400), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(300), index=True)
    actor_type: Mapped[str] = mapped_column(String(100), index=True)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    email_domain: Mapped[str | None] = mapped_column(String(200), index=True)
    vendor_reference_id: Mapped[int | None] = mapped_column(ForeignKey("vendor_references.id", ondelete="SET NULL"))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ActorAlias(Base):
    __tablename__ = "actor_aliases"
    __table_args__ = (UniqueConstraint("alias", name="uq_actor_alias_alias"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("actors.id", ondelete="CASCADE"), index=True)
    alias: Mapped[str] = mapped_column(String(400), index=True)
    alias_type: Mapped[str] = mapped_column(String(100), default="name", index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    from_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id", ondelete="SET NULL"), index=True)
    to_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id", ondelete="SET NULL"), index=True)
    channel: Mapped[str] = mapped_column(String(100), index=True)
    interaction_type: Mapped[str] = mapped_column(String(100), index=True)
    direction: Mapped[str | None] = mapped_column(String(50), index=True)
    occurred_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    subject: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        UniqueConstraint("source_message_id", "task_type", name="uq_task_message_type"),
        UniqueConstraint("source_document_id", "task_type", name="uq_task_document_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), index=True)
    task_type: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="open")
    priority: Mapped[str] = mapped_column(String(50), index=True, default="normal")
    job_number: Mapped[str | None] = mapped_column(String(100), index=True)
    owner_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id", ondelete="SET NULL"), index=True)
    counterparty_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id", ondelete="SET NULL"), index=True)
    source_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    workflow_spine: Mapped[str] = mapped_column(String(50), index=True, default="hybrid")
    workflow_stage: Mapped[str] = mapped_column(String(100), index=True, default="triage")
    human_required: Mapped[bool] = mapped_column(Boolean, index=True, default=False)
    auto_allowed: Mapped[bool] = mapped_column(Boolean, index=True, default=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text)
    source_folder_path: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    last_event_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    details_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TaskEvent(Base):
    __tablename__ = "task_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    event_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSON)


class DecisionScore(Base):
    __tablename__ = "decision_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    scored_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    action_label: Mapped[str] = mapped_column(String(200), index=True)
    score_total: Mapped[float] = mapped_column(Float, index=True)
    score_speed: Mapped[float] = mapped_column(Float)
    score_risk: Mapped[float] = mapped_column(Float)
    score_cash: Mapped[float] = mapped_column(Float)
    score_relationship: Mapped[float] = mapped_column(Float)
    score_rework: Mapped[float] = mapped_column(Float)
    weights_json: Mapped[dict | None] = mapped_column(JSON)
    rationale: Mapped[str | None] = mapped_column(Text)


class WorkflowAction(Base):
    __tablename__ = "workflow_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    action_type: Mapped[str] = mapped_column(String(100), index=True)
    action_mode: Mapped[str] = mapped_column(String(30), index=True)  # auto or human
    action_status: Mapped[str] = mapped_column(String(30), index=True, default="applied")
    actor_email: Mapped[str | None] = mapped_column(String(320), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AppUser(Base):
    __tablename__ = "app_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), index=True, default="buyer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class RfqQuote(Base):
    __tablename__ = "rfq_quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_number: Mapped[str | None] = mapped_column(String(100), index=True)
    vendor_reference_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendor_references.id", ondelete="SET NULL"), index=True
    )
    requested_by_actor_id: Mapped[int | None] = mapped_column(ForeignKey("actors.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="requested")
    request_date: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    quote_amount: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(20), default="USD")
    notes: Mapped[str | None] = mapped_column(Text)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    po_number: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    job_number: Mapped[str | None] = mapped_column(String(100), index=True)
    vendor_reference_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendor_references.id", ondelete="SET NULL"), index=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id", ondelete="SET NULL"), index=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("app_users.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="draft")
    total_amount: Mapped[float | None] = mapped_column(Float, index=True)
    approved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    issued_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    source_task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OrderConfirmation(Base):
    __tablename__ = "order_confirmations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), index=True, default="pending")
    confirmed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvoiceMatch(Base):
    __tablename__ = "invoice_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), unique=True, index=True)
    purchase_order_id: Mapped[int | None] = mapped_column(
        ForeignKey("purchase_orders.id", ondelete="SET NULL"), index=True
    )
    match_status: Mapped[str] = mapped_column(String(50), index=True, default="unmatched")
    variance_amount: Mapped[float | None] = mapped_column(Float)
    exception_reason: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class VendorKpi(Base):
    __tablename__ = "vendor_kpis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_reference_id: Mapped[int] = mapped_column(ForeignKey("vendor_references.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[str] = mapped_column(DateTime(timezone=True), index=True)
    period_end: Mapped[str] = mapped_column(DateTime(timezone=True), index=True)
    on_time_rate: Mapped[float | None] = mapped_column(Float)
    avg_cycle_days: Mapped[float | None] = mapped_column(Float)
    exception_rate: Mapped[float | None] = mapped_column(Float)
    total_spend: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LineItem(Base):
    __tablename__ = "line_items"
    __table_args__ = (UniqueConstraint("document_id", "line_no", name="uq_line_item_doc_line"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    line_no: Mapped[int] = mapped_column(Integer)
    vendor_sku: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    qty: Mapped[float | None] = mapped_column(Float)
    uom: Mapped[str | None] = mapped_column(String(50))
    unit_price: Mapped[float | None] = mapped_column(Float)
    line_total: Mapped[float | None] = mapped_column(Float)
    category_guess: Mapped[str | None] = mapped_column(String(200))


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_name: Mapped[str] = mapped_column(String(100), index=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    processed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    ended_at: Mapped[str | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict | None] = mapped_column(JSON)


class PipelineError(Base):
    __tablename__ = "pipeline_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="SET NULL"), index=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), index=True)
    message_graph_id: Mapped[str | None] = mapped_column(String(256), index=True)
    stage: Mapped[str] = mapped_column(String(100), index=True)
    error_message: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PipelineCheckpoint(Base):
    __tablename__ = "pipeline_checkpoints"
    __table_args__ = (UniqueConstraint("mailbox_id", "pipeline_name", name="uq_checkpoint_mailbox_pipeline"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int] = mapped_column(ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True)
    pipeline_name: Mapped[str] = mapped_column(String(100), index=True)
    last_successful_sync_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_id: Mapped[int | None] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="SET NULL"))
    progress_cursor: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DeadLetter(Base):
    __tablename__ = "dead_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailbox_id: Mapped[int | None] = mapped_column(ForeignKey("mailboxes.id", ondelete="SET NULL"), index=True)
    stage: Mapped[str] = mapped_column(String(100), index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=1)
    next_retry_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), index=True)
