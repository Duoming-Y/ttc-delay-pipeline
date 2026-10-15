"""Step 2 - Read the raw files and standardize their values.

Each function here takes one messy value and returns a clean one, which makes
them easy to unit-test (see tests/test_clean.py).
"""
import re

import pandas as pd

RAW_COLUMNS = ["Date", "Time", "Day", "Station", "Code", "Min Delay", "Min Gap", "Bound", "Line", "Vehicle"]


# ----- Reading ---------------------------------------------------------------
def read_raw_file(path, source_label):
    """Read one yearly file (Excel or CSV) into a DataFrame with the standard columns."""
    if path.suffix == ".xlsx":
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    df = df[RAW_COLUMNS].copy()          # drops extra columns such as the portal's "_id"
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")  # same format for every source
    df["source"] = source_label
    return df


def fix_mojibake(text):
    """Repair text that was UTF-8 encoded twice, e.g. 'DOOR PROBLEMS â\\x80\\x93 DEBRIS' -> 'DOOR PROBLEMS – DEBRIS'.

    The portal's code table contains such text. Values that are already fine are returned unchanged.
    """
    if not isinstance(text, str) or "â" not in text:
        return text
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def read_codes(path):
    """Read the delay-code lookup table as {code: description}."""
    codes = pd.read_csv(path)
    codes.columns = [c.strip().upper() for c in codes.columns]
    descriptions = codes["DESCRIPTION"].map(fix_mojibake).str.strip()
    return dict(zip(codes["CODE"].str.strip().str.upper(), descriptions))


# ----- Line ------------------------------------------------------------------
# Each pattern found in the free-text Line field points to one subway line.
_LINE_PATTERNS = [
    ("YU", r"\bYUS?\b|YONGE|UNIVERSITY|LINE ?1\b"),
    ("BD", r"\bBD\b|BLOOR|DANFORTH|LINE ?2\b|\bBL\b"),
    ("SRT", r"\bSRT\b|SCARBOROUGH|LINE ?3\b"),
    ("SHP", r"\bSHP\b|\bSHEP|SHEPPARD|LINE ?4\b"),
]


def normalize_line(value):
    """Turn values like 'YU / BD', 'BD LINE 2' or 'SHEP' into YU, BD, SRT, SHP or MULTI.

    Returns None when the value is missing or is not a subway line
    (e.g. bus routes such as '77 SWANSEA', or '999').
    """
    if value is None or pd.isna(value):
        return None
    text = str(value).upper().strip()
    # A run of 2+ digits (other than inside "LINE 1") means a bus route or an error code.
    if re.search(r"\d{2,}", text):
        return None
    found = sorted({line for line, pattern in _LINE_PATTERNS if re.search(pattern, text)})
    if not found:
        return None
    return found[0] if len(found) == 1 else "MULTI"


# ----- Station ---------------------------------------------------------------
# Canonical station names, current as of 2026 (Dundas -> TMU, Eglinton West -> Cedarvale).
STATIONS = [
    # Line 1
    "FINCH", "NORTH YORK CENTRE", "SHEPPARD-YONGE", "YORK MILLS", "LAWRENCE", "EGLINTON", "DAVISVILLE",
    "ST CLAIR", "SUMMERHILL", "ROSEDALE", "BLOOR-YONGE", "WELLESLEY", "COLLEGE", "TMU", "QUEEN", "KING",
    "UNION", "ST ANDREW", "OSGOODE", "ST PATRICK", "QUEEN'S PARK", "MUSEUM", "ST GEORGE", "SPADINA",
    "DUPONT", "ST CLAIR WEST", "CEDARVALE", "GLENCAIRN", "LAWRENCE WEST", "YORKDALE", "WILSON",
    "SHEPPARD WEST", "DOWNSVIEW PARK", "FINCH WEST", "YORK UNIVERSITY", "PIONEER VILLAGE", "HIGHWAY 407",
    "VAUGHAN METROPOLITAN CENTRE",
    # Line 2
    "KIPLING", "ISLINGTON", "ROYAL YORK", "OLD MILL", "JANE", "RUNNYMEDE", "HIGH PARK", "KEELE",
    "DUNDAS WEST", "LANSDOWNE", "DUFFERIN", "OSSINGTON", "CHRISTIE", "BATHURST", "BAY", "SHERBOURNE",
    "CASTLE FRANK", "BROADVIEW", "CHESTER", "PAPE", "DONLANDS", "GREENWOOD", "COXWELL", "WOODBINE",
    "MAIN STREET", "VICTORIA PARK", "WARDEN", "KENNEDY",
    # Line 4
    "BAYVIEW", "BESSARION", "LESLIE", "DON MILLS",
    # Line 3 (closed July 2023)
    "LAWRENCE EAST", "ELLESMERE", "MIDLAND", "SCARBOROUGH CENTRE", "MCCOWAN",
]

# Other spellings found in the data -> canonical name.
STATION_ALIASES = {
    "BLOOR": "BLOOR-YONGE", "YONGE": "BLOOR-YONGE", "BLOOR YONGE": "BLOOR-YONGE",
    "SHEPPARD": "SHEPPARD-YONGE", "SHEPPARD YONGE": "SHEPPARD-YONGE",
    "NORTH YORK CTR": "NORTH YORK CENTRE", "NORTH YORK CENTER": "NORTH YORK CENTRE",
    "VMC": "VAUGHAN METROPOLITAN CENTRE", "VAUGHAN MC": "VAUGHAN METROPOLITAN CENTRE",
    "DUNDAS": "TMU", "EGLINTON WEST": "CEDARVALE",
    "SCARBOROUGH CTR": "SCARBOROUGH CENTRE", "HWY 407": "HIGHWAY 407",
    "YONGE AND BLOOR": "BLOOR-YONGE", "BLOOR AND YONGE": "BLOOR-YONGE",
}
_STATION_LOOKUP = {name: name for name in STATIONS} | STATION_ALIASES

_YARD_WORDS = re.compile(r"YARD|CARHOUSE|WYE|BUILD.?UP|HOSTLER|DIVISION|PORTAL|TRANSIT COMMIS|HILLCREST|SHOP")
_LINE_WIDE_WORDS = re.compile(
    r"^LINE \d|YONGE\W*UNIVERSITY|BLOOR\W*DANFORTH|SHEPPARD LINE|SCARBOROUGH RAPID|SYSTEM ?WIDE")
# Line tags and truncated words that follow a station name, e.g. "KENNEDY BD PLA", "PIONEER VILLAGE STATIO".
_TRAILING_TAGS = re.compile(r"(\s+(BD|YUS|YU|SRT|SHP|PLATFORM \d|PLATFORM|PLATFO\w*|PLA|STAT\w*|STN|TO|TOWARDS))+$")


def _simplify(text):
    text = str(text).upper().strip()
    text = re.split(r"\s+TO\s+|\(|\s-\s|\s&\s|,", text)[0]   # keep the first place in "X TO Y"
    text = text.replace(".", "").replace("/", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return _TRAILING_TAGS.sub("", text).strip()


def classify_station(value):
    """Return (station, location_type) for a raw Station value.

    location_type is one of:
      STATION    - matched to a canonical subway station
      LINE_WIDE  - the record describes a whole line, not one station
      YARD       - a yard, carhouse or other non-passenger facility
      UNKNOWN    - could not be matched (kept, and flagged by validation)
    """
    if value is None or pd.isna(value):
        return None, "UNKNOWN"
    raw = str(value).upper()
    simple = _simplify(raw)
    if simple in _STATION_LOOKUP:
        return _STATION_LOOKUP[simple], "STATION"
    if _YARD_WORDS.search(raw):
        return None, "YARD"
    if _LINE_WIDE_WORDS.search(raw):
        return None, "LINE_WIDE"
    return None, "UNKNOWN"


# ----- Other fields ----------------------------------------------------------
def normalize_bound(value, valid=frozenset({"N", "S", "E", "W"})):
    """Return N/S/E/W, or None when the direction is missing or not a compass direction."""
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().upper()
    return text if text in valid else None


def parse_timestamp(date_text, time_text):
    """Combine '2024-01-31' and '7:05' into a Timestamp; returns NaT if either part is invalid."""
    return pd.to_datetime(f"{date_text} {time_text}", format="%Y-%m-%d %H:%M", errors="coerce")
