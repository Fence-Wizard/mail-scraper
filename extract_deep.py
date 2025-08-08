import os, re, json, sys, time, threading, shutil, sqlite3
from pathlib import Path
import fitz  # PyMuPDF

# ---------- Matrix rain ----------
def matrix_rain(stop_event, speed=0.06):
    if os.name == "nt":
        os.system("")
    try:
        cols, rows = shutil.get_terminal_size()
    except Exception:
        cols, rows = 80, 24
    sys.stdout.write("\033[?25l\033[1;32m"); sys.stdout.flush()
    drops = [0] * cols
    while not stop_event.is_set():
        buf=[]
        for r in range(rows):
            line=[]
            for c in range(cols):
                if drops[c] == r: line.append("1")
                elif 0 < (r - drops[c]) % rows < 8: line.append("0")
                else: line.append(" ")
            buf.append("".join(line))
        sys.stdout.write("\n".join(buf))
        sys.stdout.write("\033[F"*rows); sys.stdout.flush()
        drops = [(d+1)%rows for d in drops]; time.sleep(speed)
    sys.stdout.write("\033[0m\033[?25h\n"); sys.stdout.flush()

# ---------- config ----------
ROOT = Path("raw_data")
DB = Path("purchasing.db")

# ---------- DB schema ----------
DDL = [
    """CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE,
        vendor TEXT,
        vendor_canonical TEXT,
        po_number TEXT,
        job_number TEXT,
        invoice_number TEXT,
        invoice_date TEXT,
        subtotal REAL,
        tax REAL,
        total REAL,
        ship_to TEXT,
        ship_from TEXT,
        source_sender TEXT,
        source_received_at TEXT,
        source_subject TEXT,
        extract_notes TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS line_items(
        id INTEGER PRIMARY KEY,
        document_id INTEGER,
        line_no INTEGER,
        vendor_sku TEXT,
        description TEXT,
        qty REAL,
        uom TEXT,
        unit_price REAL,
        line_total REAL,
        category_guess TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )""",
]

def db_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA journal_mode=WAL")
    for ddl in DDL: conn.execute(ddl)
    return conn

# ---------- Generic parsing ----------
_PO  = re.compile(r'\b(?:PO|P\.O\.|Purchase\s*Order)\b[^\w]*[:#\s]*([A-Z0-9\-]{4,})', re.I)
_JOB = re.compile(r'\b(?:Job(?:\s*(?:No\.?|Number))?)\b[^\w]*[:#\s-]*([0-9]{5,})', re.I)
_INV = re.compile(r'\b(?:Invoice(?:\s*No\.?)?)\b[^\w]*[:#\s]*([A-Z0-9\-]{4,})', re.I)
_TOT = re.compile(r'\bTotal(?:\s+(?:Due|Amount))?\b', re.I)
_MON = re.compile(r'\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))')
_DAT = re.compile(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b')

def extract_text_lines(pdf_path: Path):
    doc = fitz.open(pdf_path)
    lines=[]
    for p in doc:
        lines.extend(p.get_text("text").splitlines())
    return lines

def generic_header(lines):
    joined = "\n".join(lines)
    po = (_PO.search(joined) or (None,))[1] if _PO.search(joined) else None
    job= (_JOB.search(joined) or (None,))[1] if _JOB.search(joined) else None
    inv= (_INV.search(joined) or (None,))[1] if _INV.search(joined) else None
    inv_date=None
    total=None

    # better total/date via local context
    for i, ln in enumerate(lines):
        if inv_date is None:
            md = _DAT.search(ln)
            if md: inv_date = md.group(1)
        if total is None and _TOT.search(ln):
            for look in [ln] + lines[i+1:i+3]:
                mm = _MON.search(look)
                if mm: total = mm.group(1); break
    if total is None:
        m=_MON.search(joined); total = m.group(1) if m else None

    return {
        "po_number": po,
        "job_number": job,
        "invoice_number": inv,
        "invoice_date": inv_date,
        "total": total
    }

# ---------- Vendor adapters ----------
def detect_vendor(pdf_path: Path, sender: str, subject: str) -> str:
    low = f"{pdf_path.name} {sender or ''} {subject or ''}".lower()
    if "masterhalco" in low or "master halco" in low: return "Master Halco"
    if "merchantsmetals" in low or "merchants metals" in low: return "Merchants Metals"
    if "culpeper" in low: return "Culpeper"
    if "barrette" in low: return "Barrette"
    if "afs" in low: return "AFS"
    if "fsg" in low: return "FSG"
    return "Unknown"

def parse_master_halco(lines):
    """
    Basic first-pass: many Master Halco docs label 'Order no' and 'Total due'.
    Improve as we see more samples.
    """
    joined = "\n".join(lines)
    # Try alternate terms used by their order confs
    order_no = None
    for ln in lines[:40]:
        m = re.search(r'\b(?:Order\s*(?:no|#))\b[^\w]*[:#\s]*([0-9\-]{4,})', ln, re.I)
        if m:
            order_no = m.group(1); break

    total=None
    for i, ln in enumerate(lines):
        if re.search(r'\bTotal\s*(?:due)?\b', ln, re.I):
            for look in [ln] + lines[i+1:i+3]:
                mm = _MON.search(look)
                if mm: total = mm.group(1); break
        if total: break

    # Fallbacks to generic
    gen = generic_header(lines)
    return {
        "po_number": gen["po_number"] or order_no,
        "job_number": gen["job_number"],
        "invoice_number": gen["invoice_number"],
        "invoice_date": gen["invoice_date"],
        "total": gen["total"] or total,
        "line_items": []  # fill later
    }

ADAPTERS = {
    "Master Halco": parse_master_halco,
    # Add more: "Merchants Metals": parse_merchants_metals, ...
}

# ---------- Email metadata ----------
def read_meta_for(pdf_path: Path):
    msg_id = pdf_path.parent.name.replace("_attachments","")
    meta_path = pdf_path.parent.with_name(f"{msg_id}.json")
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            meta = {}
    frm = (meta.get("from") or meta.get("from_") or {}).get("emailAddress") or {}
    sender = frm.get("address")
    rec = meta.get("receivedDateTime")
    subj= meta.get("subject")
    return sender, rec, subj

# ---------- Main extraction ----------
def find_pdfs(root: Path):
    for folder, _, files in os.walk(root):
        if folder.endswith("_attachments"):
            for f in files:
                if f.lower().endswith(".pdf"):
                    p = Path(folder) / f
                    try:
                        if p.stat().st_size > 0:
                            yield p
                    except FileNotFoundError:
                        continue

def upsert_document(conn, row):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents(file_path, vendor, vendor_canonical, po_number, job_number,
                              invoice_number, invoice_date, subtotal, tax, total,
                              ship_to, ship_from, source_sender, source_received_at,
                              source_subject, extract_notes)
        VALUES(:file_path,:vendor,:vendor_canonical,:po_number,:job_number,
               :invoice_number,:invoice_date,:subtotal,:tax,:total,
               :ship_to,:ship_from,:source_sender,:source_received_at,
               :source_subject,:extract_notes)
        ON CONFLICT(file_path) DO UPDATE SET
            vendor=excluded.vendor,
            vendor_canonical=excluded.vendor_canonical,
            po_number=excluded.po_number,
            job_number=excluded.job_number,
            invoice_number=excluded.invoice_number,
            invoice_date=excluded.invoice_date,
            total=excluded.total,
            source_sender=excluded.source_sender,
            source_received_at=excluded.source_received_at,
            source_subject=excluded.source_subject,
            extract_notes=excluded.extract_notes
    """, row)
    conn.commit()
    return cur.lastrowid or conn.execute("SELECT id FROM documents WHERE file_path=?", (row["file_path"],)).fetchone()[0]

def insert_line_items(conn, doc_id, items):
    cur = conn.cursor()
    cur.execute("DELETE FROM line_items WHERE document_id=?", (doc_id,))
    for idx, it in enumerate(items, start=1):
        cur.execute("""
            INSERT INTO line_items(document_id,line_no,vendor_sku,description,qty,uom,unit_price,line_total,category_guess)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (doc_id, idx, it.get("vendor_sku"), it.get("description"), it.get("qty"),
              it.get("uom"), it.get("unit_price"), it.get("line_total"), it.get("category_guess")))
    conn.commit()

def main():
    conn = db_conn()
    count = 0
    for pdf in find_pdfs(ROOT):
        sender, received, subject = read_meta_for(pdf)
        try:
            lines = extract_text_lines(pdf)
        except Exception as e:
            notes = f"READ_ERROR: {e}"
            row = {
                "file_path": str(pdf), "vendor": None, "vendor_canonical": None,
                "po_number": None, "job_number": None, "invoice_number": None,
                "invoice_date": None, "subtotal": None, "tax": None, "total": None,
                "ship_to": None, "ship_from": None, "source_sender": sender,
                "source_received_at": received, "source_subject": subject,
                "extract_notes": notes,
            }
            upsert_document(conn, row)
            continue

        vendor_guess = detect_vendor(pdf, sender or "", subject or "")
        adapter = ADAPTERS.get(vendor_guess)
        header = adapter(lines) if adapter else generic_header(lines)

        row = {
            "file_path": str(pdf),
            "vendor": vendor_guess,
            "vendor_canonical": vendor_guess,  # later: map aliases → canonical
            "po_number": header.get("po_number"),
            "job_number": header.get("job_number"),
            "invoice_number": header.get("invoice_number"),
            "invoice_date": header.get("invoice_date"),
            "subtotal": None,
            "tax": None,
            "total": float((header.get("total") or "0").replace(",","")) if header.get("total") else None,
            "ship_to": None,
            "ship_from": None,
            "source_sender": sender,
            "source_received_at": received,
            "source_subject": subject,
            "extract_notes": "adapter="+(vendor_guess or "generic"),
        }
        doc_id = upsert_document(conn, row)
        insert_line_items(conn, doc_id, header.get("line_items", []))
        count += 1
        if count % 50 == 0:
            print(f"Processed {count} PDFs ...", flush=True)

    print(f"✅ Completed. Documents in {DB}")

if __name__ == "__main__":
    stop_evt = threading.Event()
    t = threading.Thread(target=matrix_rain, args=(stop_evt,), daemon=True)
    t.start()
    try:
        main()
    finally:
        stop_evt.set()
        t.join()
