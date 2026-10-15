"""Write a human-readable data-quality report (reports/data_quality_report.md)."""
from datetime import date

from . import config

REASON_TEXT = {
    "duplicate_row": "Exact duplicate of an earlier row",
    "invalid_line": "Line missing or not a subway line (e.g. bus route '77 SWANSEA')",
    "invalid_timestamp": "Date/time could not be parsed",
    "negative_minutes": "Delay or gap minutes missing or negative",
}
WARNING_TEXT = {
    "unknown_delay_code": "Delay code not in the official code table",
    "unmatched_station": "Station text could not be matched to a known station, line or yard",
    "day_of_week_mismatch": "'Day' column disagrees with the date (day recomputed from the date)",
    "invalid_bound": "Direction not N/S/E/W (set to empty)",
    "extreme_delay": f"Delay longer than {config.EXTREME_DELAY_MINUTES} minutes (kept, review manually)",
}


def _pct(part, whole):
    return f"{100 * part / whole:.2f}%" if whole else "n/a"


def build_report(summary, top_unknown_codes, top_unmatched_stations):
    n_in = summary["input_rows"]
    lines = [
        "# Data Quality Report",
        "",
        f"Generated {date.today().isoformat()} by `python -m ttc_pipeline`.",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Input rows | {n_in:,} |",
        f"| Clean rows loaded | {summary['clean_rows']:,} ({_pct(summary['clean_rows'], n_in)}) |",
        f"| Rejected rows | {summary['rejected_rows']:,} ({_pct(summary['rejected_rows'], n_in)}) |",
        f"| Clean rows with at least one warning | {summary['rows_with_any_warning']:,} |",
        f"| Date range | {summary['date_range'][0]} to {summary['date_range'][1]} |",
        "",
        "Rows by source file: " + ", ".join(f"{k}: {v:,}" for k, v in summary["rows_by_source"].items()),
        "",
        "## Rejected rows (removed, saved to `data/processed/rejected_rows.csv`)",
        "",
        "| Rule | Rows | Meaning |",
        "|---|---|---|",
    ]
    for reason, count in summary["rejected_by_reason"].items():
        lines.append(f"| `{reason}` | {count:,} | {REASON_TEXT[reason]} |")
    lines += [
        "",
        "## Warnings (rows kept, listed in the `quality_flags` column)",
        "",
        "| Rule | Rows | Meaning |",
        "|---|---|---|",
    ]
    for warning, count in summary["warnings_by_type"].items():
        lines.append(f"| `{warning}` | {count:,} | {WARNING_TEXT[warning]} |")

    total = summary["clean_rows"]
    lines += [
        "",
        "## Location matching",
        "",
        "The raw `Station` field is free text (1,600+ distinct spellings). Each value is mapped to:",
        "",
        "| Location type | Rows | Share |",
        "|---|---|---|",
    ]
    for loc in ["STATION", "LINE_WIDE", "YARD", "UNKNOWN"]:
        count = summary["location_types"].get(loc, 0)
        lines.append(f"| {loc} | {count:,} | {_pct(count, total)} |")
    lines += ["", "## Most common delay codes missing from the code table", "", "| Code | Rows |", "|---|---|"]
    lines += [f"| {code} | {count:,} |" for code, count in top_unknown_codes.items()]
    lines += ["", "## Most common unmatched station values", "", "| Raw value | Rows |", "|---|---|"]
    lines += [f"| {value} | {count:,} |" for value, count in top_unmatched_stations.items()]
    return "\n".join(lines) + "\n"


def write_report(clean_df, summary, path=config.REPORTS_DIR / "data_quality_report.md"):
    flagged = clean_df["quality_flags"].fillna("")
    unknown_codes = clean_df.loc[flagged.str.contains("unknown_delay_code"), "code"].value_counts().head(10)
    unmatched = clean_df.loc[clean_df["location_type"] == "UNKNOWN", "station_raw"].value_counts().head(10)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_report(summary, unknown_codes.to_dict(), unmatched.to_dict()), encoding="utf-8")
    return path
