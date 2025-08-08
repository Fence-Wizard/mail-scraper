# decision_preview.py
# Preview how each purchasing document would flow through the decision tree.
# Requires: pip install pyyaml pandas python-dotenv (dotenv optional)

import os, re, argparse, sqlite3
from typing import Dict, Any
import pandas as pd
import yaml

DB_PATH = "purchasing.db"
YAML_PATH = "decision_tree.yml"
OUT_CSV = "decision_preview.csv"

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def approval_threshold(vendor: str, cfg: Dict[str, Any]) -> float:
    vmap = (cfg.get("globals", {}).get("vendor_overrides") or {})
    if vendor and vendor in vmap and "approval_threshold" in vmap[vendor]:
        return float(vmap[vendor]["approval_threshold"])
    return float(cfg.get("globals", {}).get("default_approval_threshold", 1000.0))

def classify(doc: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    # Required fields check
    req = cfg.get("globals", {}).get("required_fields", [])
    for field in req:
        if not doc.get(field):
            return "unknown"

    rules = cfg.get("globals", {}).get("classification", {})
    def get(field): return doc.get(field)

    # job_if
    for r in rules.get("job_if", []):
        op = r["operator"]
        field = r["field"]
        if op == "exists" and get(field):
            return "job"
        if op == "regex":
            if re.search(r["value"], str(get(field) or "")):
                return "job"

    # stock_if
    for r in rules.get("stock_if", []):
        op = r["operator"]
        field = r["field"]
        val = get(field)
        if op == "regex":
            if re.search(r["value"], str(val or "")):
                return "stock"
        if op == "domain_in":
            dom = ""
            if isinstance(val, str) and "@" in val:
                dom = val.split("@")[-1].lower()
            else:
                dom = (val or "").lower()
            domain_list = set([d.lower() for d in (r.get("value") or [])])
            if dom in domain_list:
                return "stock"

    return rules.get("default", "unknown")

def eval_condition(expr: str, ctx: Dict[str, Any], cfg: Dict[str, Any]) -> bool:
    expr = expr.strip()
    if expr == "job_number is missing":
        return not ctx.get("job_number")
    if "approval_threshold(" in expr:
        thr = approval_threshold(ctx.get("vendor") or "", cfg)
        expr = expr.replace("approval_threshold(vendor)", str(thr))
    safe_ctx = {"total": ctx.get("total", 0) or 0}
    try:
        return bool(eval(expr, {"__builtins__": {}}, safe_ctx))
    except Exception:
        return False

def pick_label(branch: str, ctx: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    branch_cfg = cfg["routing"].get(branch, {})
    rules = branch_cfg.get("rules", [])
    for r in rules:
        cond = r.get("when")
        if cond is None or eval_condition(cond, ctx, cfg):
            return r.get("name", f"{branch.upper()} – Unlabeled")
    return f"{branch.upper()} – Unmatched"

def select_docs(conn, limit: int) -> pd.DataFrame:
    q = "SELECT * FROM documents ORDER BY id DESC"
    if limit > 0:
        q += f" LIMIT {limit}"
    return pd.read_sql(q, conn)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="Max docs to preview (0=all)")
    ap.add_argument("--output", type=str, default=OUT_CSV, help="Output CSV path")
    args = ap.parse_args()

    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Not found: {DB_PATH}")
    if not os.path.exists(YAML_PATH):
        raise SystemExit(f"Not found: {YAML_PATH}")

    cfg = load_yaml(YAML_PATH)
    conn = sqlite3.connect(DB_PATH)
    df = select_docs(conn, args.limit)
    if df.empty:
        print("No documents found.")
        return

    rows = []
    for _, r in df.iterrows():
        doc = r.to_dict()
        ctx = {
            "vendor": doc.get("vendor_canonical") or doc.get("vendor"),
            "total": float(doc.get("total") or doc.get("total_amount") or 0) or 0.0,
            "job_number": doc.get("job_number"),
            "po_number": doc.get("po_number"),
            "invoice_number": doc.get("invoice_number"),
            "source_subject": doc.get("source_subject"),
            "source_sender": doc.get("source_sender"),
            "source_received_at": doc.get("source_received_at"),
        }
        branch = classify(ctx, cfg)
        label = pick_label(branch, ctx, cfg)
        thr = approval_threshold(ctx.get("vendor") or "", cfg)
        rows.append({
            "id": r.get("id"),
            "vendor": ctx["vendor"],
            "total": ctx["total"],
            "job_number": ctx["job_number"],
            "po_number": ctx["po_number"],
            "invoice_number": ctx["invoice_number"],
            "source_subject": ctx["source_subject"],
            "source_sender": ctx["source_sender"],
            "decision_branch": branch,      # unknown / stock / job
            "decision_label": label,        # human-readable label
            "approval_threshold_used": thr, # for transparency
        })

    out = pd.DataFrame(rows)
    out.to_csv(args.output, index=False)
    print(f"✅ Wrote preview: {args.output}")
    print("Columns: id, vendor, total, job_number, po_number, invoice_number, source_subject, source_sender, decision_branch, decision_label, approval_threshold_used")

if __name__ == "__main__":
    main()
