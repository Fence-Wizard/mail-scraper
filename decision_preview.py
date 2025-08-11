# decision_preview.py
# Preview how each purchasing document would flow through the decision tree.
# Outputs decision_preview.csv (no external integrations).
# Matrix-style "digital rain" displays while processing; disable with --no-matrix.

import argparse
import os
import re
import sqlite3
import sys
import threading
import time
import random
from typing import Any, Dict, List

import pandas as pd
import yaml

# colorama ensures ANSI colors render correctly on Windows
try:
    from colorama import init as colorama_init, Fore, Style
    COLORAMA = True
except Exception:
    COLORAMA = False
    class Fore:
        GREEN = ""
        RESET = ""
    class Style:
        RESET_ALL = ""

DB_PATH = "purchasing.db"
YAML_PATH = "decision_tree.yml"
OUT_CSV = "decision_preview.csv"


# --------------------------
# Matrix "digital rain"
# --------------------------
def _get_console_size(default_cols=100, default_rows=24):
    try:
        import shutil
        size = shutil.get_terminal_size((default_cols, default_rows))
        return size.columns, size.lines
    except Exception:
        return default_cols, default_rows


class MatrixRain:
    def __init__(self, fps: float = 30.0, intensity: float = 0.33):
        """intensity: fraction of columns that are active (0..1)"""
        self.running = False
        self.thread = None
        self.fps = fps
        self.intensity = max(0.05, min(0.9, intensity))
        self.columns, self.rows = _get_console_size()
        # keep at least 10 rows so the effect doesn't look broken in tiny terminals
        self.rows = max(self.rows, 10)
        # Use digits and Katakana-ish unicode to evoke the Matrix vibe
        self.charset = list("0123456789")
        # Precompute column states
        self.col_states = [self._spawn_drop() if random.random() < self.intensity else None
                           for _ in range(self.columns)]

    def _spawn_drop(self):
        return {
            "y": random.randint(-self.rows, 0),
            "speed": random.randint(1, 2),  # rows per frame
            "length": random.randint(6, max(7, self.rows // 2)),
        }

    def _frame(self):
        # Avoid spamming scrollback: draw within the screen using ANSI cursor moves
        # Clear screen on first start
        sys.stdout.write("\x1b[?25l")  # hide cursor
        for _ in range(self.rows):
            sys.stdout.write("\n")
        sys.stdout.flush()

        try:
            while self.running:
                # Resize-aware: occasionally refresh console size
                if random.random() < 0.03:
                    cols, rows = _get_console_size()
                    if cols != self.columns or rows != self.rows:
                        self.columns, self.rows = cols, max(rows, 10)
                        self.col_states = [self._spawn_drop() if random.random() < self.intensity else None
                                           for _ in range(self.columns)]

                # Build a frame buffer of spaces
                buffer = [[" "]*self.columns for _ in range(self.rows)]

                # Update columns
                for x in range(self.columns):
                    st = self.col_states[x]
                    if st is None:
                        if random.random() < self.intensity * 0.05:
                            self.col_states[x] = self._spawn_drop()
                        continue
                    y = st["y"]
                    length = st["length"]
                    # Draw the tail
                    for i in range(length):
                        ry = y - i
                        if 0 <= ry < self.rows:
                            ch = random.choice(self.charset)
                            buffer[ry][x] = ch
                    # Advance
                    st["y"] += st["speed"]
                    # Recycle
                    if st["y"] - st["length"] > self.rows:
                        if random.random() < self.intensity:
                            self.col_states[x] = self._spawn_drop()
                        else:
                            self.col_states[x] = None

                # Move cursor to top-left and render
                sys.stdout.write("\x1b[H")  # cursor home
                green = Fore.GREEN if COLORAMA else ""
                reset = Style.ResetAll if hasattr(Style, "ResetAll") else (Style.RESET_ALL if COLORAMA else "")
                for r in range(self.rows):
                    line = "".join(buffer[r])
                    sys.stdout.write(green + line + reset + "\n")
                sys.stdout.flush()
                time.sleep(1.0 / self.fps)
        finally:
            # Clear screen area and restore cursor
            sys.stdout.write("\x1b[?25h")
            sys.stdout.flush()

    def start(self):
        if self.running:
            return
        self.running = True
        if COLORAMA:
            colorama_init(autoreset=True)
        self.thread = threading.Thread(target=self._frame, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.5)
            self.thread = None


# --------------------------
# Decision logic utilities
# --------------------------
def load_yaml(path: str) -> Dict[str, Any]:
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
            domain_list = {d.lower() for d in (r.get("value") or [])}
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


def select_docs(conn: sqlite3.Connection, limit: int) -> pd.DataFrame:
    q = "SELECT * FROM documents ORDER BY id DESC"
    if limit > 0:
        q += f" LIMIT {limit}"
    return pd.read_sql(q, conn)


# --------------------------
# Main
# --------------------------
def run_preview(limit: int, output: str, no_matrix: bool) -> None:
    if not os.path.exists(DB_PATH):
        raise SystemExit(f"Not found: {DB_PATH}")
    if not os.path.exists(YAML_PATH):
        raise SystemExit(f"Not found: {YAML_PATH}")

    cfg = load_yaml(YAML_PATH)
    rain = None

    try:
        # start matrix rain if enabled and stdout is a TTY
        if not no_matrix and sys.stdout.isatty():
            rain = MatrixRain(fps=28.0, intensity=0.35)
            rain.start()

        conn = sqlite3.connect(DB_PATH)
        try:
            df = select_docs(conn, limit)
        finally:
            conn.close()

        if df.empty:
            if rain: rain.stop()
            print("No documents found.")
            return

        rows: List[Dict[str, Any]] = []
        total_docs = len(df)
        processed = 0

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

            processed += 1
            # lightweight progress line (doesn't fight the rain too much)
            if processed % 25 == 0 and sys.stdout.isatty():
                sys.stdout.write(f"\x1b[2K\r{Fore.GREEN if COLORAMA else ''}Processed {processed}/{total_docs}{Style.RESET_ALL if COLORAMA else ''}")
                sys.stdout.flush()

        # Stop animation before printing final lines
        if rain:
            rain.stop()

        out = pd.DataFrame(rows)
        out.to_csv(output, index=False, encoding="utf-8")
        print(f"\n✅ Wrote preview: {output}")
        print("Columns: id, vendor, total, job_number, po_number, invoice_number, source_subject, source_sender, decision_branch, decision_label, approval_threshold_used")

    finally:
        # Failsafe: ensure animation is off
        if 'rain' in locals() and rain:
            rain.stop()


def main():
    ap = argparse.ArgumentParser(description="Preview decision routing for purchasing documents.")
    ap.add_argument("--limit", type=int, default=200, help="Max docs to preview (0=all)")
    ap.add_argument("--output", type=str, default=OUT_CSV, help="Output CSV path")
    ap.add_argument("--no-matrix", action="store_true", help="Disable Matrix-style display")
    args = ap.parse_args()

    run_preview(limit=args.limit, output=args.output, no_matrix=args.no_matrix)


if __name__ == "__main__":
    main()
