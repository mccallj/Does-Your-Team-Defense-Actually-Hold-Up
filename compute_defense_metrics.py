"""
Defense Report Card — Metrics Computation
2025 NFL Season

Fetches 2025 PBP data via nfl_data_py (with participation stats for
offense_personnel, defenders_in_box, number_of_pass_rushers), then builds
pre-aggregated tables for the Streamlit app.

Run once before launching the app:
    python compute_defense_metrics.py

Run with --force to re-download data even if a local cache exists:
    python compute_defense_metrics.py --force
"""

import sys
import json
import argparse
import warnings
import subprocess as _sp
from pathlib import Path

# ── Auto-install required packages ───────────────────────────────────────────
# Runs at import time so all third-party packages below are guaranteed present.

def _ensure_packages():
    """Auto-install nfl_data_py/pyarrow if missing.
    Fast-fails immediately if run from any Python outside the Anaconda env,
    because pip cannot safely install scientific packages there."""
    import importlib.util

    # Guard: check the interpreter path, not just whether a package is present.
    # The system Python 3.13 may have a partial pandas install, but it cannot
    # build nfl_data_py's transitive dependencies (missing pkg_resources, etc.).
    # Any executable not under /opt/anaconda3 is the wrong environment.
    _CONDA_ENV = "/opt/anaconda3/envs/Python3127/bin/python"
    if "/opt/anaconda3" not in sys.executable:
        print(
            "\n⚠️  Wrong Python interpreter detected.\n"
            f"   Running as: {sys.executable}\n\n"
            "   This script requires the project Anaconda environment.\n"
            "   Run with:\n\n"
            f"       {_CONDA_ENV} \"{__file__}\"\n"
        )
        sys.exit(1)

    # Only auto-install packages not in the conda env baseline.
    # pandas / numpy / matplotlib ship with Anaconda — never pip-install them.
    optional = [
        ("nfl_data_py", "nfl_data_py"),
        ("pyarrow",     "pyarrow"),
    ]
    missing = [install for import_name, install in optional
               if importlib.util.find_spec(import_name) is None]
    if missing:
        print(f"Installing missing packages: {', '.join(missing)} …")
        _sp.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )
        print("  Installation complete.\n")

_ensure_packages()

# ── Third-party imports (guaranteed present after _ensure_packages) ───────────
import numpy as np
import pandas as pd
import nfl_data_py as nfl

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent.parent   # /2026 NFL Projects
LIB_DIR    = BASE_DIR / "nfl_data_library"
OUT_DIR    = Path(__file__).resolve().parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CACHE_FILE = OUT_DIR / "raw_pbp_2025.parquet"

# ── Config ────────────────────────────────────────────────────────────────────
YEAR           = 2025
MIN_CELL_PLAYS = 10   # suppress metrics for cells with fewer plays

# Import personnel grouping map from the shared data library
sys.path.insert(0, str(LIB_DIR))
from config import PERSONNEL_MAP  # noqa: E402

# ── Columns to load from base PBP parquet ────────────────────────────────────
# Participation parquet columns (offense_personnel, defenders_in_box, etc.)
# are loaded automatically via the include_participation=True merge.
NEEDED_BASE_COLS = [
    "play_id", "game_id",
    "season_type", "play_type",
    "defteam", "posteam",
    "epa", "success",
    "yards_gained", "yards_after_catch",
    "score_differential", "yardline_100",
    "qtr", "game_half",
    "down", "ydstogo",
    "touchdown", "first_down", "complete_pass",
    "pass_length", "pass_location",
    "run_gap", "run_location",
    "shotgun", "no_huddle",
    "qb_hit", "sack", "interception",
    "week",
]

# ── Fetch / Cache ─────────────────────────────────────────────────────────────

def fetch_pbp(force_refresh: bool = False) -> tuple[pd.DataFrame, bool]:
    """Download and cache PBP + participation data. Returns (df, has_participation)."""

    if CACHE_FILE.exists() and not force_refresh:
        print(f"Loading from local cache: {CACHE_FILE.name}")
        df = pd.read_parquet(CACHE_FILE)
        has_participation = "offense_personnel" in df.columns
        print(f"  Loaded {len(df):,} rows  |  personnel data: {'YES' if has_participation else 'NO (proxy mode)'}")
        return df, has_participation

    print(f"Fetching {YEAR} PBP + participation data via nfl_data_py ...")
    print("  (downloading ~150–250 MB from nflverse — this takes a few minutes)")

    try:
        raw = nfl.import_pbp_data(
            [YEAR],
            columns=NEEDED_BASE_COLS,
            include_participation=True,
            downcast=True,
        )
    except Exception as exc:
        print(f"  ERROR fetching data: {exc}")
        sys.exit(1)

    print(f"  Raw rows fetched: {len(raw):,}  |  columns: {len(raw.columns)}")

    # Check for participation columns
    participation_cols = ["offense_personnel", "defenders_in_box", "number_of_pass_rushers"]
    has_participation  = all(c in raw.columns for c in participation_cols)
    if has_participation:
        print(f"  Personnel data: FOUND  ({', '.join(participation_cols)})")
    else:
        found = [c for c in participation_cols if c in raw.columns]
        missing = [c for c in participation_cols if c not in raw.columns]
        print(f"  Personnel data: PARTIAL  found={found}  missing={missing}")
        print("  => Falling back to shotgun/run_gap proxies for unavailable columns.")
        has_participation = False

    # Filter to regular season pass and run plays
    df = raw[
        (raw["season_type"] == "REG") &
        (raw["play_type"].isin(["pass", "run"])) &
        (raw["defteam"].notna())
    ].copy().reset_index(drop=True)

    print(f"  Filtered rows: {len(df):,} (REG pass+run plays)")

    # Cache to parquet for faster subsequent runs
    print(f"  Caching to: {CACHE_FILE.name} ...")
    df.to_parquet(CACHE_FILE, index=False)

    return df, has_participation


# ── Derived columns ────────────────────────────────────────────────────────────

def add_derived(df: pd.DataFrame, has_participation: bool) -> pd.DataFrame:
    """Add all bucketed/derived columns used as groupby keys or metrics."""
    df = df.copy()

    # ── Personnel grouping (Tab 1) ────────────────────────────────────────────
    if has_participation and "offense_personnel" in df.columns:
        df["personnel_grouping"] = (
            df["offense_personnel"].map(PERSONNEL_MAP).fillna("other")
        )
    else:
        df["personnel_grouping"] = (
            df["shotgun"].fillna(0).astype(int).map({1: "Shotgun", 0: "Under Center"})
            + " " + df["play_type"].str.title()
        )

    # ── Offensive formation label ─────────────────────────────────────────────
    if "offense_formation" in df.columns:
        df["offense_formation"] = df["offense_formation"].fillna("Unknown")
    else:
        df["offense_formation"] = df["shotgun"].fillna(0).astype(int).map(
            {1: "SHOTGUN", 0: "UNDER CENTER"}
        )

    # ── Defensive front (Tab 2) — bucket defenders_in_box ───────────────────
    if has_participation and "defenders_in_box" in df.columns:
        df["def_front"] = pd.cut(
            df["defenders_in_box"].astype(float),
            bins=[0, 5, 6, 7, 99],
            labels=["Light (≤5)", "Standard (6)", "Heavy (7)", "Stacked (8+)"],
            right=True,
        ).astype(str).replace("nan", "Unknown")
        df["def_front"] = pd.Categorical(
            df["def_front"],
            categories=["Light (≤5)", "Standard (6)", "Heavy (7)", "Stacked (8+)", "Unknown"],
            ordered=True,
        )
    else:
        df["def_front"] = "N/A"

    # ── Coverage look / pass rush intensity (Tab 4) ──────────────────────────
    if has_participation and "number_of_pass_rushers" in df.columns:
        df["coverage_look"] = pd.cut(
            df["number_of_pass_rushers"].astype(float),
            bins=[0, 3, 4, 5, 99],
            labels=["Light (≤3)", "Base (4)", "Blitz (5)", "Heavy Blitz (6+)"],
            right=True,
        ).astype(str).replace("nan", "Unknown")
        df["coverage_look"] = pd.Categorical(
            df["coverage_look"],
            categories=["Light (≤3)", "Base (4)", "Blitz (5)", "Heavy Blitz (6+)", "Unknown"],
            ordered=True,
        )
    else:
        df["coverage_look"] = "N/A"

    # ── Score bucket — from DEFENSE'S TEAM perspective ───────────────────────
    # score_differential is from offense perspective; negate for defense perspective.
    # Positive def_score_margin = your team is leading.
    df["def_score_margin"] = -df["score_differential"].astype(float)
    df["score_bucket"] = pd.cut(
        df["def_score_margin"],
        bins=[-999, -14, -7, -1, 0, 6, 13, 999],
        labels=["Down Big", "Down (7-13)", "Slight Deficit", "Tied",
                "Slight Lead", "Leading (7-13)", "Up Big"],
        right=True,
    )
    df["score_bucket"] = pd.Categorical(
        df["score_bucket"].astype(str).replace("nan", "Unknown"),
        categories=["Down Big", "Down (7-13)", "Slight Deficit", "Tied",
                    "Slight Lead", "Leading (7-13)", "Up Big"],
        ordered=True,
    )

    # ── Other flags ───────────────────────────────────────────────────────────
    df["red_zone_flag"] = (
        df["yardline_100"].fillna(100).astype(float) <= 20
    ).astype(int)

    df["pressure_flag"] = (
        (df["qb_hit"].fillna(0).astype(float) == 1.0) |
        (df["sack"].fillna(0).astype(float)   == 1.0)
    ).astype(int)

    return df


# ── Shared aggregation helper ─────────────────────────────────────────────────

def _agg(df: pd.DataFrame, keys: list) -> pd.DataFrame:
    """Groupby aggregation with play count and key defensive metrics."""
    if df.empty:
        return pd.DataFrame()

    agg = (
        df.groupby(keys, dropna=False, observed=True)
        .agg(
            plays                = ("epa",           "count"),
            epa_allowed          = ("epa",           "mean"),
            success_rate_allowed = ("success",       "mean"),
            yards_allowed        = ("yards_gained",  "mean"),
            td_rate              = ("touchdown",     "mean"),
            first_down_rate      = ("first_down",    "mean"),
            pressure_rate        = ("pressure_flag", "mean"),
            interceptions        = ("interception",  "sum"),
            sacks                = ("sack",          "sum"),
        )
        .reset_index()
    )

    # YAC — only meaningful on complete pass plays
    yac = (
        df[df["complete_pass"].fillna(0).astype(float) == 1.0]
        .groupby(keys, dropna=False, observed=True)["yards_after_catch"]
        .mean()
        .reset_index(name="yac_allowed")
    )
    if not yac.empty:
        agg = agg.merge(yac, on=keys, how="left")
    else:
        agg["yac_allowed"] = np.nan

    # Suppress metrics for sparse cells
    sparse = agg["plays"] < MIN_CELL_PLAYS
    metric_cols = [
        "epa_allowed", "success_rate_allowed", "yards_allowed",
        "td_rate", "first_down_rate", "yac_allowed",
    ]
    for col in metric_cols:
        if col in agg.columns:
            agg.loc[sparse, col] = np.nan

    return agg


# ── Build individual tables ───────────────────────────────────────────────────

def build_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Season-level summary per team. Used for headline stat chips."""
    agg = _agg(df, ["defteam"])

    # League ranks (lower EPA = better defense → lower rank = better)
    agg["epa_rank"]     = agg["epa_allowed"].rank(method="min").astype("Int64")
    agg["success_rank"] = agg["success_rate_allowed"].rank(method="min").astype("Int64")
    agg["yards_rank"]   = agg["yards_allowed"].rank(method="min").astype("Int64")
    n = len(agg)
    agg["total_teams"]  = n

    # Pass / run play counts per team
    pr = (
        df.groupby(["defteam", "play_type"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    if "pass" in pr.columns:
        agg = agg.merge(pr[["defteam", "pass"]].rename(columns={"pass": "pass_plays"}),
                        on="defteam", how="left")
    if "run" in pr.columns:
        agg = agg.merge(pr[["defteam", "run"]].rename(columns={"run": "run_plays"}),
                        on="defteam", how="left")

    return agg


def build_personnel(df: pd.DataFrame) -> pd.DataFrame:
    """Tab 1 — EPA / success rate / YAC by offensive personnel grouping."""
    return _agg(df, ["defteam", "personnel_grouping"])


def build_front(df: pd.DataFrame) -> pd.DataFrame:
    """Tab 2 — Defensive front (def_front) by play type."""
    return _agg(df, ["defteam", "def_front", "play_type"])


def build_game_script(df: pd.DataFrame) -> pd.DataFrame:
    """Tab 3 — 2nd-half (Q3+Q4) EPA/success by score situation."""
    second_half = df[df["qtr"] >= 3].copy()
    return _agg(second_half, ["defteam", "score_bucket", "qtr"])


def build_redzone(df: pd.DataFrame) -> pd.DataFrame:
    """Tab 4 — Red zone efficiency by coverage look, down, and pressure."""
    rz = df[df["red_zone_flag"] == 1].copy()
    return _agg(rz, ["defteam", "coverage_look", "down", "pressure_flag"])


def build_league_avg(df: pd.DataFrame) -> dict:
    """League-wide averages used as baseline comparisons in charts."""
    rz = df[df["red_zone_flag"] == 1]
    sh = df[df["qtr"] >= 3]
    return {
        "epa_allowed":        round(float(df["epa"].mean()), 4),
        "success_rate":       round(float(df["success"].mean()), 4),
        "yards_allowed":      round(float(df["yards_gained"].mean()), 3),
        "td_rate":            round(float(df["touchdown"].mean()), 4),
        "first_down_rate":    round(float(df["first_down"].mean()), 4),
        "pressure_rate":      round(float(df["pressure_flag"].mean()), 4),
        "rz_td_rate":         round(float(rz["touchdown"].mean()), 4) if len(rz) else 0.0,
        "rz_epa":             round(float(rz["epa"].mean()), 4) if len(rz) else 0.0,
        "rz_success_rate":    round(float(rz["success"].mean()), 4) if len(rz) else 0.0,
        "sh_epa":             round(float(sh["epa"].mean()), 4) if len(sh) else 0.0,
        "sh_success_rate":    round(float(sh["success"].mean()), 4) if len(sh) else 0.0,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Build defense metrics tables.")
    parser.add_argument("--force", action="store_true",
                        help="Force re-download (ignore local cache)")
    args = parser.parse_args()

    df, has_participation = fetch_pbp(force_refresh=args.force)
    df = add_derived(df, has_participation)

    print("\nBuilding pre-aggregated tables ...")
    overview    = build_overview(df)
    personnel   = build_personnel(df)
    front       = build_front(df)
    game_script = build_game_script(df)
    redzone     = build_redzone(df)
    league_avg  = build_league_avg(df)

    # Save
    overview.to_csv(   OUT_DIR / "def_overview_2025.csv",    index=False)
    personnel.to_csv(  OUT_DIR / "def_personnel_2025.csv",   index=False)
    front.to_csv(      OUT_DIR / "def_front_2025.csv",       index=False)
    game_script.to_csv(OUT_DIR / "def_game_script_2025.csv", index=False)
    redzone.to_csv(    OUT_DIR / "def_redzone_2025.csv",     index=False)

    with open(OUT_DIR / "league_avg_2025.json", "w") as f:
        json.dump(league_avg, f, indent=2)

    print(f"\n{'─'*50}")
    print(f"  Data written to: {OUT_DIR}")
    print(f"{'─'*50}")
    print(f"  def_overview_2025.csv    — {len(overview):>4} rows")
    print(f"  def_personnel_2025.csv   — {len(personnel):>4} rows")
    print(f"  def_front_2025.csv       — {len(front):>4} rows")
    print(f"  def_game_script_2025.csv — {len(game_script):>4} rows")
    print(f"  def_redzone_2025.csv     — {len(redzone):>4} rows")
    print(f"  league_avg_2025.json")
    print(f"{'─'*50}")
    print("\nDone. Run `streamlit run app.py` to launch the app.")


if __name__ == "__main__":
    main()
