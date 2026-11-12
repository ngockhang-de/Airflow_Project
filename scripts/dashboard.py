import sys
from pathlib import Path

import pandas as pd
import sweetviz as sv


PROJECT_ROOT = Path(__file__).resolve().parents[1]

run_date = sys.argv[1] if len(sys.argv) > 1 else "20261105"

raw_file = PROJECT_ROOT / "data" / "raw" / run_date / "orders.csv"
clean_file = PROJECT_ROOT / "data" / "cleaned" / run_date / "valid_orders.csv"
report_dir = PROJECT_ROOT / "data" / "reports" / run_date

if not clean_file.exists():
    sys.exit(f"No cleaned orders file found for run date {run_date}. Please run the cleaning step first.")

raw_orders = pd.read_csv(raw_file)
clean_orders = pd.read_csv(clean_file)

report = sv.compare([raw_orders, "Raw orders"], [clean_orders, "Cleaned orders"])


report_dir.mkdir(parents=True, exist_ok=True)
report_file = report_dir / "orders_comparison.html"
report.show_html(
    str(report_file),
    open_browser=False
)
