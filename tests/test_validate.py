"""Tests for the data-quality rules in ttc_pipeline/validate.py."""
import pandas as pd

from ttc_pipeline import validate


def flags_for(clean_df, time_text):
    row = clean_df[clean_df["occurred_at"].str.endswith(time_text)]
    assert len(row) == 1, f"expected one row at {time_text}"
    return row.iloc[0]["quality_flags"].split(";")


def test_every_input_row_is_either_kept_or_rejected(sample_raw, codes):
    clean_df, rejected, summary = validate.validate(sample_raw, codes)
    assert len(clean_df) + len(rejected) == len(sample_raw)
    assert summary["input_rows"] == len(sample_raw)


def test_reject_reasons(sample_raw, codes):
    _, rejected, summary = validate.validate(sample_raw, codes)
    assert summary["rejected_by_reason"] == {
        "duplicate_row": 1, "invalid_line": 2, "invalid_timestamp": 1, "negative_minutes": 0,
    }
    assert set(rejected["reject_reason"]) == {"duplicate_row", "invalid_line", "invalid_timestamp"}


def test_negative_minutes_are_rejected(sample_raw, codes):
    sample_raw.loc[0, "Min Delay"] = -5
    _, rejected, _ = validate.validate(sample_raw, codes)
    assert "negative_minutes" in set(rejected["reject_reason"])


def test_warnings_keep_the_row_and_record_the_problem(sample_raw, codes):
    clean_df, _, summary = validate.validate(sample_raw, codes)
    assert "unknown_delay_code" in flags_for(clean_df, "10:00")
    assert "unmatched_station" in flags_for(clean_df, "11:00")
    assert "day_of_week_mismatch" in flags_for(clean_df, "12:00")
    assert "invalid_bound" in flags_for(clean_df, "13:00")
    assert "extreme_delay" in flags_for(clean_df, "14:00")
    assert summary["rows_with_any_warning"] == 5


def test_clean_rows_have_no_flags(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    assert flags_for(clean_df, "08:00") == [""]


def test_cleaned_values(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    kennedy = clean_df[clean_df["occurred_at"] == "2024-01-02 17:30"].iloc[0]
    assert kennedy["line"] == "BD"
    assert kennedy["line_name"] == "Line 2 Bloor-Danforth"
    assert kennedy["station"] == "KENNEDY"
    assert kennedy["code_description"] == "DISORDERLY PATRON"
    assert kennedy["hour"] == 17
    assert kennedy["day_of_week"] == "Tuesday"
    assert pd.isna(kennedy["vehicle"])   # 0 in the raw data means "no vehicle"


def test_wrong_weekday_is_recomputed_from_date(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    row = clean_df[clean_df["occurred_at"].str.endswith("12:00")].iloc[0]
    assert row["day_of_week"] == "Monday"     # 2024-01-01 was a Monday, raw data said Friday


def test_invalid_bound_becomes_empty(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    row = clean_df[clean_df["occurred_at"].str.endswith("13:00")].iloc[0]
    assert pd.isna(row["bound"])


def test_unknown_code_gets_placeholder_description(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    row = clean_df[clean_df["occurred_at"].str.endswith("10:00")].iloc[0]
    assert row["code_description"] == "UNKNOWN CODE"


def test_delay_ids_are_unique_and_sequential(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    assert list(clean_df["delay_id"]) == list(range(1, len(clean_df) + 1))
