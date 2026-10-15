"""Run every step in order: download -> read -> validate -> load -> analyze -> report."""
import argparse

import pandas as pd

from . import analyze, clean, config, download, load, report, validate


def run(refresh=False):
    print("1/5 Downloading raw files")
    paths = download.download_all(refresh=refresh)

    print("2/5 Reading raw files")
    frames = [clean.read_raw_file(paths[name], label) for name, label in config.DELAY_RESOURCES.items()]
    raw = pd.concat(frames, ignore_index=True)
    codes = clean.read_codes(paths[config.CODES_RESOURCE])

    print("3/5 Validating")
    clean_df, rejected_df, summary = validate.validate(raw, codes)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    clean_df.to_csv(config.PROCESSED_DIR / "delays_clean.csv", index=False)       # used by Power BI
    rejected_df.to_csv(config.PROCESSED_DIR / "rejected_rows.csv", index=False)

    print("4/5 Loading into SQLite")
    n_loaded = load.load_to_sqlite(clean_df, codes)

    print("5/5 Running KPI queries and writing reports")
    analyze.analyze()
    report_path = report.write_report(clean_df, summary)

    print(f"\nDone. {summary['input_rows']:,} input rows -> {n_loaded:,} loaded, "
          f"{summary['rejected_rows']:,} rejected, {summary['rows_with_any_warning']:,} flagged.")
    print(f"Data quality report: {report_path.relative_to(config.ROOT)}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="TTC subway delay data pipeline")
    parser.add_argument("--refresh", action="store_true", help="download the raw files again")
    run(refresh=parser.parse_args().refresh)
