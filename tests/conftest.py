"""Shared test data: a small hand-made sample that contains every kind of problem."""
import pandas as pd
import pytest

CODES = {"MUPAA": "PASSENGER ASSISTANCE ALARM ACTIVATED", "SUDP": "DISORDERLY PATRON", "EUDO": "DOOR PROBLEMS"}


def make_row(**overrides):
    row = {"Date": "2024-01-01", "Time": "08:00", "Day": "Monday", "Station": "UNION STATION", "Code": "MUPAA",
           "Min Delay": 4, "Min Gap": 8, "Bound": "S", "Line": "YU", "Vehicle": 5000, "source": "2024 file"}
    row.update(overrides)
    return row


@pytest.fixture
def codes():
    return dict(CODES)


@pytest.fixture
def sample_raw():
    rows = [
        make_row(),                                                     # 0 clean
        make_row(),                                                     # 1 exact duplicate of row 0 -> rejected
        make_row(Line="77 SWANSEA"),                                    # 2 bus route -> rejected
        make_row(Line=None, Time="09:00"),                              # 3 missing line -> rejected
        make_row(Time="25:99"),                                         # 4 bad time -> rejected
        make_row(Code="ZZZZ", Time="10:00"),                            # 5 unknown code -> warning
        make_row(Station="SOMEWHERE ODD", Time="11:00"),                # 6 unmatched station -> warning
        make_row(Day="Friday", Time="12:00"),                           # 7 wrong weekday -> warning
        make_row(Bound="B", Time="13:00"),                              # 8 invalid bound -> warning
        make_row(**{"Min Delay": 600, "Time": "14:00"}),                # 9 extreme delay -> warning
        make_row(Line="BD", Station="KENNEDY BD STATION", Code="SUDP",
                 Date="2024-01-02", Day="Tuesday", Time="17:30",
                 **{"Min Delay": 0, "Min Gap": 0}, Vehicle=0),          # 10 clean, zero-minute incident
    ]
    return pd.DataFrame(rows)
