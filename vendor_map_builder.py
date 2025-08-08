import os, re, json, csv
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path("raw_data")
CSV_SUMMARY = Path("invoice_summary.csv")  # optional
OUT_JSON = Path("vendor_map.json")

# Seed: known canonical vendors and common hints
CANONICAL = {
    "Master Halco": ["masterhalco", "master halco", "mh"],
    "Merchants Metals": ["merchantsmetals", "merchants metals", "merchants"],
    "Stephens Pipe & Steel": ["stephenspipe", "stephens pipe", "sps"],
    "AFS": ["afs"],
    "FSG": ["fsg"],
    "Culpeper": ["culpeper"],
    "Barrette": ["barrette"],
}

def domain_from_email(addr: str) -> str | None:
    if not addr or "@" not in addr: return None
    return addr.lower().split("@",1)[1]

def scan_raw_data_for_senders():
    domain_counts = Counter()
    for folder, _, files in os.walk(ROOT):
        for f in files:
            if f.endswith(".json") and not f.startswith("_"):
                p = Path(folder) / f
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                # very light extraction to avoid full json load for speed
                # but try json first for accuracy
                try:
                    import json as _json
                    data = _json.loads(text)
                    frm = (data.get("from") or data.get("from_") or {}).get("emailAddress") or {}
                    addr = frm.get("address")
                    dom = domain_from_email(addr)
                    if dom: domain_counts[dom] += 1
                except Exception:
                    # fallback: naive find
                    m = re.search(r'"address"\s*:\s*"([^"]+@[^"]+)"', text)
                    if m:
                        dom = domain_from_email(m.group(1))
                        if dom: domain_counts[dom] += 1
    return domain_counts

def read_csv_senders():
    results = Counter()
    if not CSV_SUMMARY.exists():
        return results
    try:
        with CSV_SUMMARY.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                sender = (row.get("Sender") or "").strip()
                dom = domain_from_email(sender)
                if dom: results[dom] += 1
    except Exception:
        pass
    return results

def guess_vendor_from_token(token: str) -> str | None:
    t = token.lower()
    for vendor, hints in CANONICAL.items():
        if any(h in t for h in hints):
            return vendor
    return None

def build_filename_hints():
    """
    Walk filenames to pick obvious vendor hints (e.g. masterhalco in filename).
    Returns dict[vendor] -> count
    """
    hits = Counter()
    for folder, _, files in os.walk(ROOT):
        if folder.endswith("_attachments"):
            for f in files:
                if f.lower().endswith(".pdf"):
                    vendor = guess_vendor_from_token(f)
                    if vendor:
                        hits[vendor] += 1
    return hits

def main():
    senders_from_json = scan_raw_data_for_senders()
    senders_from_csv  = read_csv_senders()
    filename_hits     = build_filename_hints()

    # Merge domain counts (CSV + JSON)
    domain_counts = senders_from_json + senders_from_csv

    # Propose a vendor map
    vendor_map = {}          # domain -> canonical vendor
    evidence = defaultdict(dict)  # for your review

    # 1) direct inference from domain tokens
    for dom, _ in domain_counts.items():
        guess = guess_vendor_from_token(dom.split(".")[0])  # leftmost label
        if guess:
            vendor_map[dom] = guess
            evidence[dom]["reason"] = "domain-hint"
        else:
            evidence[dom]["reason"] = "unknown"

    # 2) bump obvious filename-based vendors (not domain-bound)
    for vendor, cnt in filename_hits.items():
        evidence[f"filename::{vendor}"] = {"count": cnt, "reason": "filename-hint"}

    out = {
        "vendor_map": vendor_map,             # domain -> canonical vendor
        "notes": "Edit this file to add/override mappings. Keys are sender domains.",
        "domain_counts_top20": dict(domain_counts.most_common(20)),
        "filename_vendor_hits": dict(filename_hits.most_common(20)),
        "canonical_vendors": list(CANONICAL.keys()),
    }

    OUT_JSON.write_text(json.dumps(out, indent=2))
    print(f"✅ Wrote {OUT_JSON}")
    print("Top domains (for reference):")
    for d, c in domain_counts.most_common(10):
        print(f"  {d:30} {c}")
    print("\nEdit vendor_map.json to correct / add mappings, then re-run the deep extractor.")

if __name__ == "__main__":
    main()
