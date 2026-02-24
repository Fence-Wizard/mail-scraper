import os, re, csv, json, sys, time, threading, shutil
from pathlib import Path
import fitz  # PyMuPDF

# ===========================
# Matrix "digital rain" layer
# ===========================
def matrix_rain(stop_event: threading.Event, speed=0.05):
    # enable ANSI on Windows
    if os.name == "nt":
        os.system("")  # no-op but enables VT sequences in recent Windows
    # figure out screen size
    try:
        cols, rows = shutil.get_terminal_size()
    except Exception:
        cols, rows = 80, 24

    # hide cursor, set bright green
    sys.stdout.write("\033[?25l\033[1;32m")
    sys.stdout.flush()

    # one drop position per column
    drops = [0] * cols
    charset = "01"

    while not stop_event.is_set():
        # render each row once per frame
        lines = []
        for r in range(rows):
            line_chars = []
            for c in range(cols):
                line_chars.append(charset[(drops[c] == r)])
            lines.append("".join(line_chars))
        # print frame
        sys.stdout.write("\n".join(lines))
        # move cursor back up to overwrite next frame
        sys.stdout.write("\033[F" * rows)
        sys.stdout.flush()
        # advance drops
        drops = [(d + 1) % rows for d in drops]
        time.sleep(speed)

    # reset color and show cursor again
    sys.stdout.write("\033[0m\033[?25h\n")
    sys.stdout.flush()

# ===========================
# PDF parsing (unchanged core)
# ===========================
ROOT = Path("raw_data")
OUT_CSV = Path("invoice_summary.csv")
LOG_MISSES = Path("invoice_misses.log")

_PO_RE   = re.compile(r'\b(?:PO|P\.O\.|Purchase\s+Order)\b[^\w]*[:#\s]*([A-Z0-9\-]{4,})', re.I)
_JOB_RE  = re.compile(r'\b(?:Job(?:\s*(?:No\.?|Number))?)\b[^\w]*[:#\s-]*([0-9]{5,})', re.I)
_TOT_LRE = re.compile(r'\bTotal(?:\s+(?:Due|Amount))?\b', re.I)
_MONEY   = re.compile(r'\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2}))')
_DATE    = re.compile(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b')

KNOWN_VENDOR_HINTS = {
    "masterhalco": "Master Halco",
    "merchantsmetals": "Merchants Metals",
    "stephenspipe": "Stephens Pipe & Steel",
    "ameristarfence": "Ameristar",
    "fasco": "Fasco",
}

def read_message_metadata(attachment_dir: Path):
    meta = {"sender": None, "receivedDateTime": None, "subject": None}
    candidates = []
    # Legacy layout companion JSON: <graph_message_id>.json beside <graph_message_id>_attachments dir.
    msg_id = attachment_dir.name.replace("_attachments", "")
    candidates.append(attachment_dir.with_name(f"{msg_id}.json"))
    # New layout has compact folder names and no local message JSON companion today.
    # Keep this fallback for future compatibility if metadata sidecars are added.
    candidates.append(attachment_dir / "message.json")

    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8", errors="ignore"))
            frm = data.get("from") or data.get("from_") or {}
            email = (frm.get("emailAddress") or {}).get("address")
            meta["sender"] = email
            meta["receivedDateTime"] = data.get("receivedDateTime")
            meta["subject"] = data.get("subject")
            break
        except Exception:
            continue
    return meta

def infer_vendor_from(sender: str | None, filename: str):
    if sender:
        s = sender.lower()
        for key, name in KNOWN_VENDOR_HINTS.items():
            if key in s:
                return name
        if "@" in s:
            return s.split("@", 1)[1]
    base = re.sub(r'[_\-]+', ' ', Path(filename).stem)
    words = [w for w in base.split() if w.lower() not in {"order","confirmation","invoice","from","po"}]
    return " ".join(words[:4]) or "Unknown"

def extract_fields_from_pdf(pdf_path: Path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc:
        lines.extend(page.get_text("text").splitlines())
    joined = "\n".join(lines)

    po = job = total = inv_date = None

    for i, line in enumerate(lines):
        if po is None:
            m = _PO_RE.search(line)
            if m and m.group(1).lower() != "job":
                po = m.group(1)
        if job is None:
            m = _JOB_RE.search(line)
            if m:
                job = m.group(1)
        if total is None and _TOT_LRE.search(line):
            for ln in [line] + lines[i+1:i+3]:
                mm = _MONEY.search(ln)
                if mm:
                    total = mm.group(1); break
        if inv_date is None:
            md = _DATE.search(line)
            if md:
                inv_date = md.group(1)

    # doc-level fallbacks
    if po is None:
        m = _PO_RE.search(joined);       po = m.group(1) if m else None
    if job is None:
        m = _JOB_RE.search(joined);      job = m.group(1) if m else None
    if total is None:
        m = _MONEY.search(joined);       total = m.group(1) if m else None
    if inv_date is None:
        m = _DATE.search(joined);        inv_date = m.group(1) if m else None

    return po, job, total, inv_date

def find_all_pdfs(root: Path):
    # Support both legacy and new downloader layouts:
    # - legacy: raw_data/.../<graph_message_id>_attachments/*.pdf
    # - current: raw_data/.../m<message_pk>_<hash>/*.pdf
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*.pdf") if p.is_file())

def main():
    pdfs = find_all_pdfs(ROOT)
    if not pdfs:
        print("No PDFs found under raw_data. Verify paths.", flush=True)
        return

    rows, misses = [], []
    for pdf in pdfs:
        meta = read_message_metadata(pdf.parent)
        po, job, total, inv_date = extract_fields_from_pdf(pdf)
        vendor = infer_vendor_from(meta.get("sender"), pdf.name)

        row = {
            "File": str(pdf),
            "Vendor": vendor,
            "PO Number": po,
            "Job Number": job,
            "Total Amount": total,
            "Invoice Date": inv_date,
            "Sender": meta.get("sender"),
            "Received": meta.get("receivedDateTime"),
            "Subject": meta.get("subject"),
        }
        rows.append(row)
        if not (po and total):
            misses.append(row)

        print(f"Parsed: {pdf.name} | Vendor={vendor} PO={po} Total={total}", flush=True)

    # Write CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    if misses:
        with LOG_MISSES.open("w", encoding="utf-8") as f:
            for m in misses:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

    print(f"\n✅ Wrote {len(rows)} rows to {OUT_CSV}")
    if misses:
        print(f"⚠️ {len(misses)} file(s) missing PO or Total → see {LOG_MISSES}")

if __name__ == "__main__":
    # Start Matrix rain in the background
    stop_evt = threading.Event()
    t = threading.Thread(target=matrix_rain, args=(stop_evt,), daemon=True)
    t.start()
    try:
        main()
    finally:
        # stop rain and wait for thread to finish
        stop_evt.set()
        t.join()
