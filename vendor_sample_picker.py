import os, re, csv, shutil
from pathlib import Path
import json

ROOT = Path("raw_data")
OUT_DIR = Path("samples")
OUT_DIR.mkdir(exist_ok=True, parents=True)

PRIORITY = [
    "master halco", "merchants metals", "afs", "fsg", "culpeper", "barrette"
]
# map common hints → canonical vendor
HINTS = {
    "masterhalco": "Master Halco",
    "master halco": "Master Halco",
    "merchantsmetals": "Merchants Metals",
    "merchants metals": "Merchants Metals",
    "stephenspipe": "Stephens Pipe & Steel",
    "afs": "AFS",
    "fsg": "FSG",
    "culpeper": "Culpeper",
    "barrette": "Barrette",
}

def read_meta(attachments_dir: Path):
    msg_id = attachments_dir.name.replace("_attachments", "")
    meta_path = attachments_dir.with_name(f"{msg_id}.json")
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return {}
    return {}

def infer_vendor(pdf_path: Path, meta: dict) -> str:
    # sender domain first
    sender = (((meta.get("from") or meta.get("from_") or {}).get("emailAddress") or {}).get("address") or "")
    s = sender.lower()
    for k, v in HINTS.items():
        if k in s:
            return v
    # filename fallback
    base = pdf_path.stem.lower()
    for k, v in HINTS.items():
        if k in base:
            return v
    # subject fallback
    subj = (meta.get("subject") or "").lower()
    for k, v in HINTS.items():
        if k in subj:
            return v
    return "Unknown"

def find_pdfs(root: Path):
    for folder, _, files in os.walk(root):
        if folder.endswith("_attachments"):
            for f in files:
                if f.lower().endswith(".pdf"):
                    yield Path(folder) / f

def main():
    picked = {v: 0 for v in set(HINTS.values())}
    rows = []
    for pdf in find_pdfs(ROOT):
        meta = read_meta(pdf.parent)
        vendor = infer_vendor(pdf, meta)
        if vendor == "Unknown":
            continue
        if vendor.lower() not in [v.lower() for v in PRIORITY]:
            continue
        if picked[vendor] >= 3:
            continue
        # copy file
        dest_dir = OUT_DIR / vendor.replace(" ", "_")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / pdf.name
        try:
            shutil.copy2(pdf, dest)
            picked[vendor] += 1
            rows.append({
                "vendor": vendor,
                "source_pdf": str(pdf),
                "copied_to": str(dest),
            })
            print(f"Picked: {vendor} -> {dest}")
        except Exception as e:
            print(f"Skip {pdf}: {e}")

    # write manifest
    with (OUT_DIR / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["vendor","source_pdf","copied_to"])
        w.writeheader()
        w.writerows(rows)

    print("\nDone. See samples/manifest.csv")

if __name__ == "__main__":
    main()
