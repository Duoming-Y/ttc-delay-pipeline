"""Project-wide settings: file locations, data sources and validation thresholds."""
from pathlib import Path

# ----- Folders ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"              # files exactly as downloaded
PROCESSED_DIR = DATA_DIR / "processed"  # cleaned outputs (CSV for Power BI)
DB_PATH = DATA_DIR / "ttc_delays.db"    # SQLite database
REPORTS_DIR = ROOT / "reports"
KPI_DIR = REPORTS_DIR / "kpis"
FIGURES_DIR = REPORTS_DIR / "figures"
SQL_DIR = ROOT / "sql"

# ----- Data source: City of Toronto Open Data (CKAN API) ---------------------
CKAN_BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
PACKAGE_ID = "ttc-subway-delay-data"

# Resource names on the portal -> label used in this project.
DELAY_RESOURCES = {
    "ttc-subway-delay-data-2023": "2023",
    "ttc-subway-delay-data-2024": "2024",
    "TTC Subway Delay Data since 2025.csv": "2025+",
}
CODES_RESOURCE = "Code Descriptions.csv"

# ----- Validation settings ---------------------------------------------------
VALID_BOUNDS = {"N", "S", "E", "W"}
EXTREME_DELAY_MINUTES = 300  # delays longer than 5 hours are kept but flagged

LINE_NAMES = {
    "YU": "Line 1 Yonge-University",
    "BD": "Line 2 Bloor-Danforth",
    "SRT": "Line 3 Scarborough RT",
    "SHP": "Line 4 Sheppard",
    "MULTI": "Multiple lines",
}
