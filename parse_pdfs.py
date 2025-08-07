import os
import re
import logging
from pathlib import Path
from pdfminer.high_level import extract_text

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ATTACHMENT_ROOT = Path("raw_data")
MAX_PDFS = 1

def extract_fields(text):
    # Field patterns
    po_match = re.search(r'\b(?:PO|P\.O\.|Purchase Order)[\s#:]*([A-Z0-9\-]+)', text, re.IGNORECASE)
    job_match = re.search(r'\bJob[\s#:]*([0-9]{6,})', text, re.IGNORECASE)
    total_match = re.search(r'Total\s+(?:Due|Amount|)\s*[:\s]*\$?([0-9,]+\.\d{2})', text, re.IGNORECASE)
    date_match = re.search(r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4})', text)

    # Heuristic: vendor = top few lines
    vendor = "\n".join(text.strip().splitlines()[:5])

    return {
        "Vendor": vendor.strip(),
        "PO Number": po_match.group(1) if po_match else None,
        "Job Number": job_match.group(1) if job_match else None,
        "Total Amount": total_match.group(1) if total_match else None,
        "Invoice Date": date_match.group(1) if date_match else None,
    }

def find_first_pdf(root_dir: Path):
    for folder, _, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                return Path(folder) / f
    return None

if __name__ == "__main__":
    logger.info("🔍 Scanning for first PDF to parse...")
    pdf_path = find_first_pdf(ATTACHMENT_ROOT)

    if not pdf_path:
        logger.warning("No PDF found in attachment folders.")
        exit()

    logger.info(f"📄 Parsing PDF: {pdf_path.name}")
    try:
        raw_text = extract_text(pdf_path)
        fields = extract_fields(raw_text)

        print("\n🧾 Extracted Fields:")
        for key, value in fields.items():
            print(f"{key}: {value if value else '❌ Not found'}")

    except Exception as e:
        logger.error(f"❌ Failed to parse {pdf_path.name}: {e}")
