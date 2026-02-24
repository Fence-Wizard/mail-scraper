import argparse
import asyncio
import json
from pathlib import Path

from .config import settings
from .logging_utils import configure_logging
from .operations import (
    run_apply_low_risk_autopilot,
    run_audit,
    run_build_role_graph,
    run_download_attachments,
    run_derive_tasks,
    run_define_task_completion_rules,
    run_export_score_profiles,
    run_ingest,
    run_import_vendors,
    run_load_extracted_csv,
    run_legacy_extract,
    run_legacy_summarize,
    run_publish_role_insights,
    run_reliability_report,
    run_replay_dead_letters,
    run_score_decisions,
    run_seed_procurement_mvp,
    run_validate_workflow_scenarios,
)
from .sqlite_port import migrate_sqlite_to_postgres


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mail-scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Run incremental Graph->Postgres message ingest.")
    ingest.add_argument("--mailbox-key", type=str, default=None)
    ingest.add_argument("--limit", type=int, default=None)
    ingest.add_argument("--matrix", action="store_true", help="Enable Matrix-style running numbers display.")

    dl = sub.add_parser("download-attachments", help="Download attachment files for ingested messages.")
    dl.add_argument("--mailbox-key", type=str, default=None)
    dl.add_argument("--limit", type=int, default=None)
    dl.add_argument("--batch-size", type=int, default=None, help="Commit and checkpoint every N messages.")
    dl.add_argument("--matrix", action="store_true", help="Enable Matrix-style running numbers display.")

    sub.add_parser("extract", help="Run legacy extract_deep parser over downloaded files.")
    load = sub.add_parser("load-extracted-csv", help="Load invoice_summary.csv into Postgres documents table.")
    load.add_argument("--csv-path", type=Path, default=Path("invoice_summary.csv"))
    import_vendors = sub.add_parser("import-vendors", help="Load vendor reference workbook into lookup table.")
    import_vendors.add_argument("--workbook", type=Path, default=Path("Vendors List.xlsx"))
    import_vendors.add_argument("--sheet", type=str, default="Data")
    sub.add_parser("build-role-graph", help="Build actor aliases and interaction graph from current data.")
    sub.add_parser("derive-tasks", help="Derive first-pass tasks from messages/documents.")
    insights = sub.add_parser("publish-role-insights", help="Generate role demand/nuance insight artifacts.")
    insights.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    rules = sub.add_parser("define-task-rules", help="Write proposed task completion and escalation rules.")
    rules.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    sub.add_parser("seed-procurement-mvp", help="Seed procurement MVP tables from derived tasks.")
    sub.add_parser("apply-low-risk-autopilot", help="Apply low-risk auto actions to open workflow tasks.")
    validate = sub.add_parser("validate-workflow-scenarios", help="Validate hybrid workflow behavior and export summary.")
    validate.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    profiles = sub.add_parser("export-score-profiles", help="Export policy scoring profiles for game-theory tuning.")
    profiles.add_argument("--output-dir", type=Path, default=Path("analysis_output"))
    score = sub.add_parser("score-decisions", help="Score task actions using payoff weights.")
    score.add_argument("--speed-weight", type=float, default=1.0)
    score.add_argument("--risk-weight", type=float, default=1.0)
    score.add_argument("--cash-weight", type=float, default=1.0)
    score.add_argument("--relationship-weight", type=float, default=1.0)
    score.add_argument("--rework-weight", type=float, default=1.0)
    sub.add_parser("summarize", help="Run legacy post_run_summary report.")
    sub.add_parser("audit", help="Show mailbox/pipeline counters from Postgres.")

    replay = sub.add_parser("replay-dead-letters", help="Mark dead letters replayed/resolved.")
    replay.add_argument("--stage", type=str, default=None)
    replay.add_argument("--limit", type=int, default=100)

    report = sub.add_parser("reliability-report", help="Print rolling pipeline failure rates.")
    report.add_argument("--window", type=int, default=20)

    port = sub.add_parser("port-sqlite", help="Port documents/line_items from purchasing.db to Postgres.")
    port.add_argument("--sqlite-path", type=Path, default=Path("purchasing.db"))

    sub.add_parser("show-config", help="Print parsed mailbox configuration.")

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_logging(settings.debug)
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "ingest":
        processed = asyncio.run(run_ingest(limit=args.limit, mailbox_key=args.mailbox_key, matrix=args.matrix))
        print(f"Ingest complete. Processed new messages: {processed}")
        return 0
    if args.command == "download-attachments":
        processed = asyncio.run(
            run_download_attachments(
                limit=args.limit,
                mailbox_key=args.mailbox_key,
                matrix=args.matrix,
                batch_size=args.batch_size,
            )
        )
        print(f"Attachment download complete. Files processed: {processed}")
        return 0
    if args.command == "extract":
        run_legacy_extract()
        return 0
    if args.command == "load-extracted-csv":
        results = run_load_extracted_csv(csv_path=args.csv_path)
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "import-vendors":
        results = run_import_vendors(vendor_workbook=args.workbook, sheet_name=args.sheet)
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "build-role-graph":
        results = run_build_role_graph()
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "derive-tasks":
        results = run_derive_tasks()
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "publish-role-insights":
        results = run_publish_role_insights(output_dir=args.output_dir)
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "define-task-rules":
        path = run_define_task_completion_rules(output_dir=args.output_dir)
        print(f"Rules written: {path}")
        return 0
    if args.command == "seed-procurement-mvp":
        results = run_seed_procurement_mvp()
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "apply-low-risk-autopilot":
        results = run_apply_low_risk_autopilot()
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "validate-workflow-scenarios":
        results = run_validate_workflow_scenarios(output_dir=args.output_dir)
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "export-score-profiles":
        path = run_export_score_profiles(output_dir=args.output_dir)
        print(f"Profiles written: {path}")
        return 0
    if args.command == "score-decisions":
        results = run_score_decisions(
            speed_weight=args.speed_weight,
            risk_weight=args.risk_weight,
            cash_weight=args.cash_weight,
            relationship_weight=args.relationship_weight,
            rework_weight=args.rework_weight,
        )
        print(json.dumps(results, indent=2))
        return 0
    if args.command == "summarize":
        run_legacy_summarize()
        return 0
    if args.command == "audit":
        counters = run_audit()
        print(json.dumps(counters, indent=2))
        return 0
    if args.command == "replay-dead-letters":
        replayed = run_replay_dead_letters(stage=args.stage, limit=args.limit)
        print(f"Dead letters replayed/resolved: {replayed}")
        return 0
    if args.command == "reliability-report":
        report = run_reliability_report(window=args.window)
        print(json.dumps(report, indent=2))
        return 0
    if args.command == "port-sqlite":
        migrate_sqlite_to_postgres(args.sqlite_path)
        return 0
    if args.command == "show-config":
        mailboxes = [mailbox.model_dump() for mailbox in settings.mailbox_configs()]
        print(json.dumps(mailboxes, indent=2))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
