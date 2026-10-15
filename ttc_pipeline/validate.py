"""Step 3 - Apply data-quality rules.

Two kinds of rule:
  * REJECT rules remove a row; it goes to rejected_rows.csv with the reason.
  * WARNING rules keep the row but record the problem in `quality_flags`,
    so analysts can include or exclude flagged rows themselves.
Nothing is dropped silently: every input row ends up in exactly one output.
"""
from collections import Counter

import pandas as pd

from . import clean, config

REJECT_REASONS = ["duplicate_row", "invalid_line", "invalid_timestamp", "negative_minutes"]
WARNING_TYPES = ["unknown_delay_code", "unmatched_station", "day_of_week_mismatch",
                 "invalid_bound", "extreme_delay"]


def validate(raw, codes, extreme_minutes=config.EXTREME_DELAY_MINUTES):
    """Clean and check the combined raw data.

    Parameters
    ----------
    raw : DataFrame with clean.RAW_COLUMNS plus `source`
    codes : dict {delay code: description}

    Returns (clean_df, rejected_df, summary dict)
    """
    df = raw.reset_index(drop=True).copy()
    reason = pd.Series(pd.NA, index=df.index, dtype="object")   # first reject reason per row

    def reject(mask, why):
        reason[mask & reason.isna()] = why

    # --- REJECT rules ----------------------------------------------------------
    reject(df.duplicated(subset=clean.RAW_COLUMNS, keep="first"), "duplicate_row")

    df["line"] = df["Line"].map(clean.normalize_line)
    reject(df["line"].isna(), "invalid_line")

    df["occurred_at"] = [clean.parse_timestamp(d, t) for d, t in zip(df["Date"], df["Time"])]
    reject(df["occurred_at"].isna(), "invalid_timestamp")

    min_delay = pd.to_numeric(df["Min Delay"], errors="coerce")
    min_gap = pd.to_numeric(df["Min Gap"], errors="coerce")
    reject(min_delay.isna() | min_gap.isna() | (min_delay < 0) | (min_gap < 0), "negative_minutes")

    rejected = raw.reset_index(drop=True)[reason.notna()].copy()
    rejected["reject_reason"] = reason[reason.notna()]

    # --- Build clean rows --------------------------------------------------------
    keep = reason.isna()
    out = pd.DataFrame(index=df.index[keep])
    out["occurred_at"] = df.loc[keep, "occurred_at"]
    out["date"] = out["occurred_at"].dt.strftime("%Y-%m-%d")
    out["year"] = out["occurred_at"].dt.year
    out["month"] = out["occurred_at"].dt.strftime("%Y-%m")
    out["hour"] = out["occurred_at"].dt.hour
    out["day_of_week"] = out["occurred_at"].dt.day_name()   # recomputed from the date
    out["line"] = df.loc[keep, "line"]
    out["line_name"] = out["line"].map(config.LINE_NAMES)

    stations = df.loc[keep, "Station"].map(clean.classify_station)
    out["station_raw"] = df.loc[keep, "Station"].astype(str).str.strip()
    out["station"] = [s for s, _ in stations]
    out["location_type"] = [t for _, t in stations]

    out["code"] = df.loc[keep, "Code"].astype(str).str.strip().str.upper()
    out["code_description"] = out["code"].map(codes)
    out["min_delay"] = min_delay[keep].astype(int)
    out["min_gap"] = min_gap[keep].astype(int)
    out["bound"] = df.loc[keep, "Bound"].map(lambda b: clean.normalize_bound(b, config.VALID_BOUNDS))
    vehicle = pd.to_numeric(df.loc[keep, "Vehicle"], errors="coerce")
    out["vehicle"] = vehicle.where(vehicle > 0).astype("Int64")   # 0 means "no vehicle"
    out["source"] = df.loc[keep, "source"]

    # --- WARNING rules -----------------------------------------------------------
    flags = {i: [] for i in out.index}

    def warn(mask, what):
        for i in out.index[mask]:
            flags[i].append(what)

    warn(out["code_description"].isna(), "unknown_delay_code")
    warn(out["location_type"] == "UNKNOWN", "unmatched_station")
    warn(out["day_of_week"] != df.loc[keep, "Day"].astype(str).str.strip(), "day_of_week_mismatch")
    raw_bound = df.loc[keep, "Bound"]
    warn(raw_bound.notna() & out["bound"].isna(), "invalid_bound")
    warn(out["min_delay"] > extreme_minutes, "extreme_delay")

    out["code_description"] = out["code_description"].fillna("UNKNOWN CODE")
    out["quality_flags"] = [";".join(flags[i]) for i in out.index]
    out["occurred_at"] = out["occurred_at"].dt.strftime("%Y-%m-%d %H:%M")
    out = out.sort_values("occurred_at").reset_index(drop=True)
    out.insert(0, "delay_id", range(1, len(out) + 1))

    warning_counts = Counter(f for fl in out["quality_flags"] if fl for f in fl.split(";"))
    summary = {
        "input_rows": len(df),
        "clean_rows": len(out),
        "rejected_rows": len(rejected),
        "rejected_by_reason": {r: int((rejected["reject_reason"] == r).sum()) for r in REJECT_REASONS},
        "warnings_by_type": {w: int(warning_counts.get(w, 0)) for w in WARNING_TYPES},
        "rows_with_any_warning": int((out["quality_flags"] != "").sum()),
        "location_types": out["location_type"].value_counts().to_dict(),
        "rows_by_source": df["source"].value_counts().sort_index().to_dict(),
        "date_range": (out["date"].min(), out["date"].max()) if len(out) else (None, None),
    }
    return out, rejected, summary
