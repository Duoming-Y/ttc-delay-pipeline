"""Load the sample into an in-memory SQLite database and check the SQL KPI results."""
import sqlite3

import pytest

from ttc_pipeline import analyze, load, validate


@pytest.fixture
def conn(sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    connection = sqlite3.connect(":memory:")      # a throwaway database that lives only in RAM
    load.load_into_connection(connection, clean_df, codes)
    yield connection
    connection.close()


@pytest.fixture
def kpis(conn):
    return analyze.run_kpis(conn)


def test_all_clean_rows_are_loaded(conn, sample_raw, codes):
    clean_df, _, _ = validate.validate(sample_raw, codes)
    assert conn.execute("SELECT COUNT(*) FROM delays").fetchone()[0] == len(clean_df)
    assert conn.execute("SELECT COUNT(*) FROM delay_codes").fetchone()[0] == len(codes)


def test_database_rejects_negative_delay(conn):
    """The CHECK constraint in schema.sql is a second line of defence after validation."""
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO delays (occurred_at, date, year, month, hour, day_of_week, line, line_name, "
            "location_type, code, code_description, min_delay, min_gap, source, quality_flags) "
            "VALUES ('2024-01-01 08:00', '2024-01-01', 2024, '2024-01', 8, 'Monday', 'YU', 'x', "
            "'STATION', 'X', 'x', -1, 0, 'test', '')")


def test_named_queries_are_parsed():
    queries = analyze.parse_named_queries("-- name: a\nSELECT 1;\n\n-- name: b\nSELECT 2;\n")
    assert queries == {"a": "SELECT 1", "b": "SELECT 2"}


def test_every_kpi_query_runs(kpis):
    expected = {"delays_by_line", "top_stations", "top_causes", "delays_by_hour",
                "delays_by_day_of_week", "monthly_trend", "yearly_summary"}
    assert set(kpis) == expected


def test_line_totals_match_raw_rows(kpis, conn):
    by_line = kpis["delays_by_line"].set_index("line_name")
    assert by_line["incidents"].sum() == conn.execute("SELECT COUNT(*) FROM delays").fetchone()[0]
    assert by_line.loc["Line 2 Bloor-Danforth", "incidents"] == 1
    assert by_line.loc["Line 2 Bloor-Danforth", "delayed_incidents"] == 0   # its only incident was 0 minutes
    # Line 1 rows in the sample: 4 + 4 + 4 + 4 + 4 + 600 minutes
    assert by_line.loc["Line 1 Yonge-University", "delay_minutes"] == 620


def test_top_causes_ignore_zero_minute_incidents(kpis):
    assert "SUDP" not in set(kpis["top_causes"]["code"])


def test_hourly_kpi_covers_only_hours_present(kpis):
    assert set(kpis["delays_by_hour"]["hour"]) == {8, 10, 11, 12, 13, 14, 17}
