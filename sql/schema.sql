-- Tables created by ttc_pipeline/load.py

DROP TABLE IF EXISTS delays;
DROP TABLE IF EXISTS delay_codes;

-- One row per delay incident that passed validation.
CREATE TABLE delays (
    delay_id         INTEGER PRIMARY KEY,
    occurred_at      TEXT    NOT NULL,      -- 'YYYY-MM-DD HH:MM'
    date             TEXT    NOT NULL,
    year             INTEGER NOT NULL,
    month            TEXT    NOT NULL,      -- 'YYYY-MM'
    hour             INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week      TEXT    NOT NULL,
    line             TEXT    NOT NULL,      -- YU, BD, SRT, SHP or MULTI
    line_name        TEXT    NOT NULL,
    station_raw      TEXT,                  -- original text, kept for auditing
    station          TEXT,                  -- canonical name, NULL unless location_type = 'STATION'
    location_type    TEXT    NOT NULL,      -- STATION, LINE_WIDE, YARD or UNKNOWN
    code             TEXT    NOT NULL,
    code_description TEXT    NOT NULL,
    min_delay        INTEGER NOT NULL CHECK (min_delay >= 0),
    min_gap          INTEGER NOT NULL CHECK (min_gap >= 0),
    bound            TEXT,                  -- N, S, E, W or NULL
    vehicle          INTEGER,
    source           TEXT    NOT NULL,      -- which yearly file the row came from
    quality_flags    TEXT    NOT NULL       -- ';'-separated warnings, '' if none
);

CREATE INDEX idx_delays_line ON delays (line);
CREATE INDEX idx_delays_station ON delays (station);
CREATE INDEX idx_delays_month ON delays (month);

-- Official delay-code lookup from the open data portal.
CREATE TABLE delay_codes (
    code        TEXT PRIMARY KEY,
    description TEXT NOT NULL
);
