"""Unit tests for the value-standardizing functions in ttc_pipeline/clean.py."""
import pandas as pd
import pytest

from ttc_pipeline import clean


@pytest.mark.parametrize("raw, expected", [
    ("YU", "YU"),
    ("YUS", "YU"),
    ("BD", "BD"),
    ("BD LINE 2", "BD"),
    ("LINE 1", "YU"),
    ("SHP", "SHP"),
    ("SHEP", "SHP"),
    ("SRT", "SRT"),
    ("YU/BD", "MULTI"),
    ("YU / BD", "MULTI"),
    ("BD/YUS", "MULTI"),
    ("YU & BD", "MULTI"),
    ("BLOOR DANFORTH & YONGE", "MULTI"),
    ("  yu  ", "YU"),            # case and spaces do not matter
])
def test_normalize_line_recognizes_subway_lines(raw, expected):
    assert clean.normalize_line(raw) == expected


@pytest.mark.parametrize("raw", ["77 SWANSEA", "999", "109 RANEE", "TRACK LEVEL ACTIVITY", "", None, float("nan")])
def test_normalize_line_rejects_non_subway_values(raw):
    assert clean.normalize_line(raw) is None


@pytest.mark.parametrize("raw, station", [
    ("BLOOR STATION", "BLOOR-YONGE"),
    ("YONGE BD STATION", "BLOOR-YONGE"),
    ("KENNEDY BD STATION", "KENNEDY"),
    ("KENNEDY SRT STATION", "KENNEDY"),
    ("ST. GEORGE YUS STATION", "ST GEORGE"),
    ("SHEPPARD STATION", "SHEPPARD-YONGE"),
    ("VMC STATION", "VAUGHAN METROPOLITAN CENTRE"),
    ("DUNDAS STATION", "TMU"),               # renamed in 2024
    ("DUNDAS WEST STATION", "DUNDAS WEST"),  # must NOT become TMU
    ("PIONEER VILLAGE STATIO", "PIONEER VILLAGE"),   # source truncates at 22 characters
    ("UNION STATION TO KING", "UNION"),
    ("KIPLING PLATFORM", "KIPLING"),
    ("QUEEN'S PARK STATION", "QUEEN'S PARK"),
])
def test_classify_station_matches_known_stations(raw, station):
    assert clean.classify_station(raw) == (station, "STATION")


@pytest.mark.parametrize("raw, location_type", [
    ("GREENWOOD YARD", "YARD"),
    ("DAVISVILLE BUILD-UP", "YARD"),
    ("WILSON CARHOUSE", "YARD"),
    ("LINE 1 YONGE-UNIVERSIT", "LINE_WIDE"),
    ("YONGE-UNIVERSITY AND B", "LINE_WIDE"),
    ("BLOOR DANFORTH SUBWAY", "LINE_WIDE"),
    ("120 CARTWRIGHT AVE", "UNKNOWN"),
    (None, "UNKNOWN"),
])
def test_classify_station_other_location_types(raw, location_type):
    station, loc = clean.classify_station(raw)
    assert loc == location_type
    assert station is None


@pytest.mark.parametrize("raw, expected", [("N", "N"), (" s ", "S"), ("B", None), ("", None), (None, None)])
def test_normalize_bound(raw, expected):
    assert clean.normalize_bound(raw) == expected


def test_parse_timestamp_valid():
    assert clean.parse_timestamp("2024-03-05", "7:05") == pd.Timestamp("2024-03-05 07:05")


@pytest.mark.parametrize("date_text, time_text", [("2024-13-01", "07:05"), ("2024-03-05", "25:00"), ("", "")])
def test_parse_timestamp_invalid_returns_nat(date_text, time_text):
    assert pd.isna(clean.parse_timestamp(date_text, time_text))


def test_fix_mojibake_repairs_double_encoded_dash():
    assert clean.fix_mojibake("DOOR PROBLEMS â\x80\x93 DEBRIS RELATED") == "DOOR PROBLEMS – DEBRIS RELATED"


def test_fix_mojibake_leaves_clean_text_alone():
    assert clean.fix_mojibake("DISORDERLY PATRON") == "DISORDERLY PATRON"
    assert clean.fix_mojibake(None) is None
