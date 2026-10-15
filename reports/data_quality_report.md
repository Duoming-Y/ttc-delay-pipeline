# Data Quality Report

Generated 2026-10-15 by `python -m ttc_pipeline`.

## Overview

| Metric | Value |
|---|---|
| Input rows | 94,891 |
| Clean rows loaded | 94,512 (99.60%) |
| Rejected rows | 379 (0.40%) |
| Clean rows with at least one warning | 3,462 |
| Date range | 2023-01-01 to 2026-08-31 |

Rows by source file: 2023: 22,949, 2024: 26,467, 2025+: 45,475

## Rejected rows (removed, saved to `data/processed/rejected_rows.csv`)

| Rule | Rows | Meaning |
|---|---|---|
| `duplicate_row` | 89 | Exact duplicate of an earlier row |
| `invalid_line` | 290 | Line missing or not a subway line (e.g. bus route '77 SWANSEA') |
| `invalid_timestamp` | 0 | Date/time could not be parsed |
| `negative_minutes` | 0 | Delay or gap minutes missing or negative |

## Warnings (rows kept, listed in the `quality_flags` column)

| Rule | Rows | Meaning |
|---|---|---|
| `unknown_delay_code` | 2,492 | Delay code not in the official code table |
| `unmatched_station` | 876 | Station text could not be matched to a known station, line or yard |
| `day_of_week_mismatch` | 60 | 'Day' column disagrees with the date (day recomputed from the date) |
| `invalid_bound` | 126 | Direction not N/S/E/W (set to empty) |
| `extreme_delay` | 21 | Delay longer than 300 minutes (kept, review manually) |

## Location matching

The raw `Station` field is free text (1,600+ distinct spellings). Each value is mapped to:

| Location type | Rows | Share |
|---|---|---|
| STATION | 90,527 | 95.78% |
| LINE_WIDE | 2,098 | 2.22% |
| YARD | 1,011 | 1.07% |
| UNKNOWN | 876 | 0.93% |

## Most common delay codes missing from the code table

| Code | Rows |
|---|---|
| SUL | 1,128 |
| PUTO | 335 |
| MRO | 248 |
| MUINF | 190 |
| ERTC | 79 |
| MRTO | 54 |
| SRO | 35 |
| MUSE | 33 |
| PUFA | 32 |
| SRDP | 29 |

## Most common unmatched station values

| Raw value | Rows |
|---|---|
| TRACK LEVEL ACTIVITY | 13 |
| OSSINGTON CENTRE TRACK | 8 |
| KENNEDY BD STATION- PL | 8 |
| EARLY ACCESS CLOSURE - | 8 |
| BROADVIEW CENTRE TRACK | 7 |
| YONGE UNIVESITY LINE | 7 |
| YUS | 7 |
| UNION STATION TOWARD S | 7 |
| VMC STATION PLATFORM # | 7 |
| FINCH STATION- PLAT 1 | 7 |
