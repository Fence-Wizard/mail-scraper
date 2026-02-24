"""Legacy wrapper for audit command."""

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parent / "src"
if SRC_PATH.exists() and str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from mail_scraper.operations import run_audit


def main() -> None:
    counters = run_audit()
    print("Mailbox/Pipeline Audit")
    for key, value in counters.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
