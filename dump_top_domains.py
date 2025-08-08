import os, json, re
from pathlib import Path
from collections import Counter

ROOT = Path("raw_data")
counter = Counter()

def email_domain(addr: str) -> str | None:
    if not addr or "@" not in addr:
        return None
    return addr.lower().split("@", 1)[1]

for folder, _, files in os.walk(ROOT):
    for f in files:
        if f.endswith(".json") and not f.startswith("_"):
            p = Path(folder) / f
            try:
                data = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
                frm = (data.get("from") or data.get("from_") or {}).get("emailAddress") or {}
                addr = frm.get("address")
                dom = email_domain(addr)
                if dom:
                    counter[dom] += 1
            except Exception:
                # fallback regex if JSON fails
                m = re.search(r'"address"\s*:\s*"([^"]+@[^"]+)"', p.read_text(errors="ignore"))
                if m:
                    dom = email_domain(m.group(1))
                    if dom:
                        counter[dom] += 1

print("Top 50 sender domains:")
for dom, count in counter.most_common(50):
    print(f"{dom:40} {count}")
