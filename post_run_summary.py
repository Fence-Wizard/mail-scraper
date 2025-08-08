# post_run_summary.py
# One-shot analyzer for purchasing.db
# - Creates clean views
# - Runs core analyses
# - Exports CSVs and an Excel workbook
# - Writes a Markdown summary

import os, sys, sqlite3, math
from datetime import datetime
import pandas as pd

DB_PATH = "purchasing.db"
OUT_DIR = "analysis_output"
EXCEL_PATH = os.path.join(OUT_DIR, "purchasing_summary.xlsx")
SUMMARY_MD = os.path.join(OUT_DIR, "purchasing_summary.md")

os.makedirs(OUT_DIR, exist_ok=True)

def table_exists(conn, name):
    return pd.read_sql(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?;",
        conn, params=(name,)
    ).shape[0] > 0

def col_exists(conn, table, col):
    df = pd.read_sql(f"PRAGMA table_info({table});", conn)
    return (df['name'] == col).any()

def safe_read_sql(conn, sql, params=None):
    try:
        return pd.read_sql(sql, conn, params=params or ())
    except Exception as e:
        return pd.DataFrame({"_error":[str(e)]})

def create_views(conn):
    # Build a clean documents view if possible
    docs_cols = pd.read_sql("PRAGMA table_info(documents);", conn)['name'].tolist() if table_exists(conn, 'documents') else []
    if not docs_cols:
        return

    # Try to be resilient to column naming
    vendor_col = 'vendor_canonical' if 'vendor_canonical' in docs_cols else ('vendor' if 'vendor' in docs_cols else None)
    total_col  = 'total' if 'total' in docs_cols else ('total_amount' if 'total_amount' in docs_cols else None)
    date_col   = 'invoice_date' if 'invoice_date' in docs_cols else None

    # Build CREATE VIEW dynamically
    select_cols = []
    for c in ['id','file_path','po_number','job_number','invoice_number','source_sender','source_received_at','source_subject','extract_notes','subtotal','tax']:
        if c in docs_cols:
            select_cols.append(c)
    if vendor_col: select_cols.append(f"{vendor_col} AS vendor")
    if total_col:  select_cols.append(f"CAST({total_col} AS REAL) AS total")
    if date_col:   select_cols.append(f"date({date_col}) AS invoice_date")

    if vendor_col and total_col:
        sql = f"""
        CREATE VIEW IF NOT EXISTS v_docs_clean AS
        SELECT {", ".join(select_cols)}
        FROM documents
        WHERE {total_col} IS NOT NULL
        """
        conn.execute("DROP VIEW IF EXISTS v_docs_clean;")
        conn.execute(sql)

    # Line items view if present
    if table_exists(conn, 'line_items'):
        conn.execute("DROP VIEW IF EXISTS v_line_items;")
        join = """
        CREATE VIEW IF NOT EXISTS v_line_items AS
        SELECT li.*,
               d.{vcol} AS vendor,
               date(d.{dcol}) AS invoice_date,
               d.job_number,
               d.po_number
        FROM line_items li
        JOIN documents d ON d.id = li.document_id
        """.format(
            vcol = vendor_col or 'vendor',
            dcol = date_col or 'invoice_date'
        )
        conn.execute(join)

def pct(x, total):
    return f"{(100.0 * x / total):.1f}%" if total and not math.isnan(total) and total > 0 else "0.0%"

def main():
    if not os.path.exists(DB_PATH):
        print(f"❌ Not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON;")

    # 1) Existence checks
    has_docs = table_exists(conn, 'documents')
    has_items = table_exists(conn, 'line_items')
    has_errs = table_exists(conn, 'errors')

    if not has_docs:
        print("❌ 'documents' table not found. Nothing to summarize.")
        sys.exit(1)

    # 2) Create views
    create_views(conn)

    # 3) Basic volumes
    docs_count = pd.read_sql("SELECT COUNT(*) AS n FROM documents", conn)['n'][0]
    items_count = pd.read_sql("SELECT COUNT(*) AS n FROM line_items", conn)['n'][0] if has_items else 0
    errs_count = pd.read_sql("SELECT COUNT(*) AS n FROM errors", conn)['n'][0] if has_errs else 0

    # 4) Completeness metrics (be resilient to columns)
    comp_sql_parts = ["SELECT"]
    docs_cols = pd.read_sql("PRAGMA table_info(documents);", conn)['name'].tolist()

    checks = []
    for col in ['vendor','vendor_canonical','po_number','job_number','invoice_date','total','total_amount']:
        if col in docs_cols:
            if col in ('total','total_amount'):
                checks.append(f"SUM(CASE WHEN {col} IS NOT NULL THEN 1 ELSE 0 END)*1.0/COUNT(*) AS pct_{col}")
            else:
                checks.append(f"SUM(CASE WHEN {col} IS NOT NULL AND {col}<>'' THEN 1 ELSE 0 END)*1.0/COUNT(*) AS pct_{col}")
    comp_sql = "SELECT " + ", ".join(checks) + " FROM documents" if checks else None
    completeness = safe_read_sql(conn, comp_sql) if comp_sql else pd.DataFrame()

    # 5) Top vendors by spend (try v_docs_clean first)
    if 'v_docs_clean' in pd.read_sql("SELECT name FROM sqlite_master WHERE type='view';", conn)['name'].tolist():
        top_vendors = safe_read_sql(conn, """
            SELECT vendor, COUNT(*) AS doc_count, SUM(total) AS total_spent
            FROM v_docs_clean
            GROUP BY vendor
            ORDER BY total_spent DESC
            LIMIT 25;
        """)
        monthly_vendor = safe_read_sql(conn, """
            SELECT strftime('%Y-%m', invoice_date) AS ym, vendor, SUM(total) AS spend
            FROM v_docs_clean
            GROUP BY ym, vendor
            ORDER BY ym DESC, spend DESC
            LIMIT 240;
        """)
        top_jobs = safe_read_sql(conn, """
            SELECT job_number, COUNT(*) AS docs, SUM(total) AS spend
            FROM v_docs_clean
            WHERE job_number IS NOT NULL AND job_number <> ''
            GROUP BY job_number
            ORDER BY spend DESC
            LIMIT 50;
        """)
    else:
        # Fallback if we couldn't build the view
        total_col = 'total' if col_exists(conn,'documents','total') else 'total_amount'
        vendor_col = 'vendor_canonical' if col_exists(conn,'documents','vendor_canonical') else 'vendor'
        date_col = 'invoice_date' if col_exists(conn,'documents','invoice_date') else None

        top_vendors = safe_read_sql(conn, f"""
            SELECT {vendor_col} AS vendor, COUNT(*) AS doc_count, SUM(CAST({total_col} AS REAL)) AS total_spent
            FROM documents
            WHERE {total_col} IS NOT NULL
            GROUP BY {vendor_col}
            ORDER BY total_spent DESC
            LIMIT 25;
        """)
        if date_col:
            monthly_vendor = safe_read_sql(conn, f"""
                SELECT strftime('%Y-%m', date({date_col})) AS ym, {vendor_col} AS vendor,
                       SUM(CAST({total_col} AS REAL)) AS spend
                FROM documents
                WHERE {total_col} IS NOT NULL
                GROUP BY ym, {vendor_col}
                ORDER BY ym DESC, spend DESC
                LIMIT 240;
            """)
        else:
            monthly_vendor = pd.DataFrame()
        top_jobs = pd.DataFrame()  # skip if no view and we don't know column names

    # 6) Line items analysis (only if exists)
    if has_items and 'v_line_items' in pd.read_sql("SELECT name FROM sqlite_master WHERE type='view';", conn)['name'].tolist():
        top_items = safe_read_sql(conn, """
            SELECT COALESCE(description, '(blank)') AS description,
                   COUNT(*) AS lines, SUM(COALESCE(total_price,0)) AS spend
            FROM v_line_items
            GROUP BY description
            ORDER BY lines DESC
            LIMIT 50;
        """)
        vendor_item_spend = safe_read_sql(conn, """
            SELECT vendor, COALESCE(description, '(blank)') AS description,
                   SUM(COALESCE(total_price,0)) AS spend
            FROM v_line_items
            GROUP BY vendor, description
            ORDER BY spend DESC
            LIMIT 200;
        """)
    else:
        top_items = pd.DataFrame()
        vendor_item_spend = pd.DataFrame()

    # 7) Errors breakdown
    if has_errs and col_exists(conn,'errors','error_message'):
        error_breakdown = safe_read_sql(conn, """
            SELECT substr(error_message,1,120) AS error_snippet, COUNT(*) AS n
            FROM errors
            GROUP BY error_snippet
            ORDER BY n DESC
            LIMIT 25;
        """)
    else:
        error_breakdown = pd.DataFrame()

    conn.close()

    # 8) Write CSVs
    def write_csv(df, name):
        if not isinstance(df, pd.DataFrame) or df.empty:
            return
        df.to_csv(os.path.join(OUT_DIR, name), index=False)

    write_csv(top_vendors, "top_vendors.csv")
    write_csv(monthly_vendor, "monthly_vendor_spend.csv")
    write_csv(top_jobs, "top_jobs_by_spend.csv")
    write_csv(top_items, "top_line_items.csv")
    write_csv(vendor_item_spend, "vendor_item_spend.csv")
    write_csv(error_breakdown, "error_breakdown.csv")

    # 9) Write Excel workbook
    with pd.ExcelWriter(EXCEL_PATH, engine="xlsxwriter") as xw:
        for name, df in [
            ("Top Vendors", top_vendors),
            ("Monthly Vendor Spend", monthly_vendor),
            ("Top Jobs by Spend", top_jobs),
            ("Top Line Items", top_items),
            ("Vendor x Item Spend", vendor_item_spend),
            ("Errors", error_breakdown),
        ]:
            if isinstance(df, pd.DataFrame) and not df.empty:
                df.to_excel(xw, sheet_name=name[:31], index=False)

    # 10) Markdown summary
    lines = []
    lines.append(f"# Purchasing Summary\n")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
    lines.append(f"- Documents: **{docs_count}**")
    lines.append(f"- Line items: **{items_count}**")
    lines.append(f"- Errors: **{errs_count}**\n")

    if isinstance(completeness, pd.DataFrame) and not completeness.empty:
        lines.append("## Field Completeness (share of non-null rows)\n")
        row = completeness.iloc[0].to_dict()
        for k, v in row.items():
            if pd.isna(v): continue
            lines.append(f"- {k}: **{v*100:.1f}%**")
        lines.append("")

    if isinstance(top_vendors, pd.DataFrame) and not top_vendors.empty:
        lines.append("## Top Vendors by Spend (first 10)\n")
        for i, r in top_vendors.head(10).iterrows():
            vendor = str(r.get('vendor','(unknown)'))
            spent  = r.get('total_spent', 0) or 0
            lines.append(f"- {vendor}: ${spent:,.2f}")
        lines.append("")

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("✅ Analysis complete.")
    print(f"• CSVs: {OUT_DIR}\\*.csv")
    print(f"• Excel: {EXCEL_PATH}")
    print(f"• Summary: {SUMMARY_MD}")

if __name__ == "__main__":
    main()
