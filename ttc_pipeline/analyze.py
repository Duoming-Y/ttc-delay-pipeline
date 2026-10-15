"""Step 5 - Run the KPI queries in sql/kpis.sql and draw charts."""
import re
import sqlite3

import matplotlib

matplotlib.use("Agg")  # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd

from . import config

KPI_FILE = config.SQL_DIR / "kpis.sql"


def parse_named_queries(sql_text):
    """Split a .sql file into {name: query} using '-- name: <name>' markers."""
    parts = re.split(r"^--\s*name:\s*(\w+)\s*$", sql_text, flags=re.MULTILINE)
    # parts = [header, name1, query1, name2, query2, ...]
    return {name: query.strip().rstrip(";") for name, query in zip(parts[1::2], parts[2::2])}


def run_kpis(conn):
    """Run every named query and return {name: DataFrame}."""
    queries = parse_named_queries(KPI_FILE.read_text(encoding="utf-8"))
    return {name: pd.read_sql_query(query, conn) for name, query in queries.items()}


def save_kpis(results, out_dir=config.KPI_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in results.items():
        df.to_csv(out_dir / f"{name}.csv", index=False)


def _barh(df, label_col, value_col, title, path, xlabel):
    fig, ax = plt.subplots(figsize=(8, 5))
    data = df.sort_values(value_col)
    ax.barh(data[label_col], data[value_col], color="#2f6db5")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def make_charts(results, out_dir=config.FIGURES_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)

    _barh(results["top_stations"].head(10), "station", "delay_minutes",
          "Top 10 stations by total delay minutes", out_dir / "top_stations.png", "Delay minutes")

    causes = results["top_causes"].head(10).copy()
    causes["label"] = causes["code_description"].str.title().str.slice(0, 40)
    _barh(causes, "label", "delay_minutes", "Top 10 delay causes by total delay minutes",
          out_dir / "top_causes.png", "Delay minutes")

    hourly = results["delays_by_hour"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(hourly["hour"], hourly["delayed_incidents"], color="#2f6db5")
    ax.set_title("Delayed incidents by hour of day")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Incidents with delay > 0 min")
    ax.set_xticks(range(0, 24, 2))
    fig.tight_layout()
    fig.savefig(out_dir / "delays_by_hour.png", dpi=120)
    plt.close(fig)

    monthly = results["monthly_trend"]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(pd.to_datetime(monthly["month"]), monthly["delay_minutes"], marker="o", markersize=3, color="#2f6db5")
    ax.set_title("Total delay minutes per month")
    ax.set_ylabel("Delay minutes")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out_dir / "monthly_trend.png", dpi=120)
    plt.close(fig)


def analyze(db_path=config.DB_PATH):
    with sqlite3.connect(db_path) as conn:
        results = run_kpis(conn)
    save_kpis(results)
    make_charts(results)
    return results
