"""
Defense Report Card — Static Infographic Generator
2025 NFL Season

Generates a shareable PNG infographic for one or all 32 NFL teams.

Usage:
    python generate_infographic.py --team KC          # single team
    python generate_infographic.py                    # all 32 teams
    python generate_infographic.py --team SF --year 2025
"""

import argparse
import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
DATA_DIR    = SCRIPT_DIR / "data"
ASSETS_DIR  = SCRIPT_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

YEAR = 2025

# ── Team config ───────────────────────────────────────────────────────────────
TEAM_PRIMARY = {
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#5B2FBE",
    "BUF": "#00338D", "CAR": "#0085CA", "CHI": "#E87722",
    "CIN": "#FB4F14", "CLE": "#FF3C00", "DAL": "#003594",
    "DEN": "#FB4F14", "DET": "#0076B6", "GB":  "#203731",
    "HOU": "#03202F", "IND": "#002C5F", "JAX": "#006778",
    "KC":  "#E31837", "LAC": "#0080C6", "LAR": "#003594",
    "LV":  "#A5ACAF", "MIA": "#008E97", "MIN": "#4F2683",
    "NE":  "#002244", "NO":  "#9F8958", "NYG": "#0B2265",
    "NYJ": "#125740", "PHI": "#004C54", "PIT": "#FFB612",
    "SEA": "#69BE28", "SF":  "#AA0000", "TB":  "#D50A0A",
    "TEN": "#0C2340", "WAS": "#5A1414",
}

TEAM_NAMES = {
    "ARI": "Arizona Cardinals",    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",     "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",   "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",       "DEN": "Denver Broncos",
    "DET": "Detroit Lions",        "GB":  "Green Bay Packers",
    "HOU": "Houston Texans",       "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC":  "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV":  "Las Vegas Raiders",    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",    "NE":  "New England Patriots",
    "NO":  "New Orleans Saints",   "NYG": "New York Giants",
    "NYJ": "New York Jets",        "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",  "SEA": "Seattle Seahawks",
    "SF":  "San Francisco 49ers",  "TB":  "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",     "WAS": "Washington Commanders",
}

# ── Style constants ────────────────────────────────────────────────────────────
BG_COLOR    = "#FAFAF8"
CARD_COLOR  = "#FFFFFF"
TXT_DARK    = "#111827"
TXT_MUTED   = "#6B7280"
TXT_FAINT   = "#9CA3AF"
GRID_COLOR  = "#E5E7EB"
STEM_ALPHA  = 0.4
DOT_SIZE    = 80
AVG_COLOR   = "#9CA3AF"
FONT_TITLE  = "DejaVu Serif"   # closest to Playfair Display in matplotlib
FONT_BODY   = "DejaVu Sans"


def hex_to_rgb_float(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


# ── Data loading ──────────────────────────────────────────────────────────────

def load_data():
    overview    = pd.read_csv(DATA_DIR / "def_overview_2025.csv")
    personnel   = pd.read_csv(DATA_DIR / "def_personnel_2025.csv")
    front       = pd.read_csv(DATA_DIR / "def_front_2025.csv")
    game_script = pd.read_csv(DATA_DIR / "def_game_script_2025.csv")
    redzone     = pd.read_csv(DATA_DIR / "def_redzone_2025.csv")
    with open(DATA_DIR / "league_avg_2025.json") as f:
        league_avg = json.load(f)
    return overview, personnel, front, game_script, redzone, league_avg


# ── Lollipop helper ───────────────────────────────────────────────────────────

def draw_lollipop(ax, categories, values, color, avg_val=None,
                  x_label="", show_values=True, x_fmt="{:.3f}"):
    """Draw a horizontal lollipop chart on a given Axes."""
    ax.set_facecolor(CARD_COLOR)
    valid = [(c, v) for c, v in zip(categories, values) if not pd.isna(v)]
    if not valid:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                color=TXT_MUTED, fontsize=9, transform=ax.transAxes)
        return

    cats, vals = zip(*valid)
    y_pos = range(len(cats))

    # Stems
    for yi, (cat, val) in enumerate(zip(cats, vals)):
        ax.hlines(yi, 0, val, color=TXT_FAINT, linewidth=1.5, alpha=STEM_ALPHA)

    # Dots
    ax.scatter(vals, y_pos, color=color, s=DOT_SIZE, zorder=5,
               edgecolors="white", linewidths=1.5)

    # League avg line
    if avg_val is not None:
        ax.axvline(avg_val, color=AVG_COLOR, linestyle="--",
                   linewidth=1.2, alpha=0.8, zorder=3)
        ax.text(avg_val, len(cats) - 0.35, "Lg avg",
                ha="center", va="top", fontsize=7, color=TXT_MUTED,
                fontfamily=FONT_BODY)

    # Zero reference line
    ax.axvline(0, color=GRID_COLOR, linewidth=0.8, alpha=0.7)

    # Value annotations
    if show_values:
        for yi, val in enumerate(vals):
            ax.text(val + 0.002, yi, x_fmt.format(val),
                    va="center", fontsize=7.5, color=TXT_MUTED,
                    fontfamily=FONT_BODY)

    # Styling
    ax.set_yticks(y_pos)
    ax.set_yticklabels(cats, fontsize=9, fontfamily=FONT_BODY, color=TXT_DARK)
    ax.set_xlabel(x_label, fontsize=8, color=TXT_MUTED, fontfamily=FONT_BODY)
    ax.tick_params(axis="x", labelsize=8, colors=TXT_MUTED)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.xaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)


def draw_grouped_bar(ax, df_chart, x_col, y_cols, y_labels, colors, x_fmt="{:.2f}"):
    """Draw a grouped horizontal bar chart."""
    ax.set_facecolor(CARD_COLOR)
    df_chart = df_chart.copy()
    cats = df_chart[x_col].tolist()
    n    = len(cats)
    n_groups = len(y_cols)
    bar_h    = 0.35
    offsets  = np.linspace(-(n_groups - 1) * bar_h / 2, (n_groups - 1) * bar_h / 2, n_groups)

    for yi, (y_col, y_label, bar_color, offset) in enumerate(
            zip(y_cols, y_labels, colors, offsets)):
        if y_col not in df_chart.columns:
            continue
        vals = df_chart[y_col].tolist()
        y_pos = [i + offset for i in range(n)]
        bars = ax.barh(y_pos, vals, height=bar_h * 0.85,
                       color=bar_color, label=y_label, alpha=0.85)

    ax.set_yticks(range(n))
    ax.set_yticklabels(cats, fontsize=9, fontfamily=FONT_BODY, color=TXT_DARK)
    ax.tick_params(axis="x", labelsize=8, colors=TXT_MUTED)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.grid(axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(fontsize=7, frameon=False, labelcolor=TXT_MUTED)


# ── Panel builders ────────────────────────────────────────────────────────────

def panel_personnel(ax, df_personnel, team, color, league_avg):
    """Panel 1 — EPA by personnel grouping (lollipop)."""
    df = df_personnel[df_personnel["defteam"] == team].copy()
    df = df.sort_values("plays", ascending=True)   # ascending so top = most plays
    df = df.tail(6)   # top 6 most-common groupings

    cats = df["personnel_grouping"].astype(str).tolist()
    vals = df["epa_allowed"].tolist()
    avg  = league_avg.get("epa_allowed")

    draw_lollipop(ax, cats, vals, color, avg_val=avg,
                  x_label="EPA / play", x_fmt="{:+.3f}")
    ax.set_title("Personnel Matchups\nEPA Allowed", fontsize=11,
                 fontfamily=FONT_TITLE, color=TXT_DARK, pad=8, loc="left",
                 fontweight="bold")


def panel_front(ax, df_front, team, color, league_avg):
    """Panel 2 — Yards allowed by defensive front × pass/run (grouped bars)."""
    df = df_front[df_front["defteam"] == team].copy()

    FRONT_ORDER = ["Light (≤5)", "Standard (6)", "Heavy (7)", "Stacked (8+)"]
    df_pass = df[df["play_type"] == "pass"].set_index("def_front")
    df_run  = df[df["play_type"] == "run"].set_index("def_front")

    rows = []
    for front in FRONT_ORDER:
        p_yds = df_pass.loc[front, "yards_allowed"] if front in df_pass.index else np.nan
        r_yds = df_run.loc[front, "yards_allowed"]  if front in df_run.index  else np.nan
        rows.append({"front": front, "pass_yds": p_yds, "run_yds": r_yds})

    chart_df = pd.DataFrame(rows).dropna(subset=["pass_yds", "run_yds"], how="all")
    if chart_df.empty:
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                color=TXT_MUTED, fontsize=9, transform=ax.transAxes)
        ax.set_facecolor(CARD_COLOR)
        return

    r, g, b = hex_to_rgb_float(color)
    draw_grouped_bar(
        ax, chart_df, "front",
        y_cols    = ["pass_yds", "run_yds"],
        y_labels  = ["Pass", "Run"],
        colors    = [color, (r, g, b, 0.45)],
    )
    ax.set_title("Defensive Front\nYards Allowed (pass vs run)", fontsize=11,
                 fontfamily=FONT_TITLE, color=TXT_DARK, pad=8, loc="left",
                 fontweight="bold")
    ax.set_xlabel("Yards / play", fontsize=8, color=TXT_MUTED, fontfamily=FONT_BODY)


def panel_game_script(ax, df_gs, team, color, league_avg):
    """Panel 3 — 2nd-half EPA by score bucket (lollipop, horizontal)."""
    df = df_gs[df_gs["defteam"] == team].copy()

    SCORE_ORDER = ["Down Big", "Down (7-13)", "Slight Deficit", "Tied",
                   "Slight Lead", "Leading (7-13)", "Up Big"]

    combined = (
        df.groupby("score_bucket")
        .apply(lambda g: pd.Series({
            "plays":       int(g["plays"].sum()),
            "epa_allowed": (
                np.average(g["epa_allowed"].dropna(),
                           weights=g.loc[g["epa_allowed"].notna(), "plays"])
                if g["epa_allowed"].notna().any() else np.nan
            ),
        }))
        .reset_index()
    )
    combined["score_bucket"] = pd.Categorical(
        combined["score_bucket"], categories=SCORE_ORDER, ordered=True
    )
    combined = combined.sort_values("score_bucket")

    cats = combined["score_bucket"].astype(str).tolist()
    vals = combined["epa_allowed"].tolist()
    avg  = league_avg.get("sh_epa")

    draw_lollipop(ax, cats, vals, color, avg_val=avg,
                  x_label="EPA / play  (2nd half)", x_fmt="{:+.3f}")
    ax.set_title("Game Script (2nd Half)\nEPA by Score Situation", fontsize=11,
                 fontfamily=FONT_TITLE, color=TXT_DARK, pad=8, loc="left",
                 fontweight="bold")


def panel_redzone(ax, df_rz, team, color, league_avg):
    """Panel 4 — Red zone TD rate by coverage look (lollipop)."""
    df = df_rz[df_rz["defteam"] == team].copy()

    COVERAGE_ORDER = ["Light (≤3)", "Base (4)", "Blitz (5)", "Heavy Blitz (6+)"]

    cov = (
        df.groupby("coverage_look")
        .apply(lambda g: pd.Series({
            "plays":   int(g["plays"].sum()),
            "td_rate": (
                np.average(g["td_rate"].dropna(),
                           weights=g.loc[g["td_rate"].notna(), "plays"])
                if g["td_rate"].notna().any() else np.nan
            ),
        }))
        .reset_index()
    )
    cov["coverage_look"] = pd.Categorical(
        cov["coverage_look"], categories=COVERAGE_ORDER, ordered=True
    )
    cov = cov.sort_values("coverage_look")

    cats = cov["coverage_look"].astype(str).tolist()
    vals = cov["td_rate"].tolist()
    avg  = league_avg.get("rz_td_rate")

    draw_lollipop(ax, cats, vals, color, avg_val=avg,
                  x_label="TD rate in red zone", x_fmt="{:.1%}")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.set_title("Red Zone Efficiency\nTD Rate by Pass-Rush Look", fontsize=11,
                 fontfamily=FONT_TITLE, color=TXT_DARK, pad=8, loc="left",
                 fontweight="bold")


# ── Main infographic builder ──────────────────────────────────────────────────

def generate(team: str, overview, personnel, front, game_script, redzone, league_avg):
    color     = TEAM_PRIMARY.get(team, "#4B5563")
    full_name = TEAM_NAMES.get(team, team)
    rgb_color = hex_to_rgb_float(color)

    # ── Figure layout: header strip + 2×2 grid ───────────────────────────────
    fig = plt.figure(figsize=(14, 18), dpi=150, facecolor=BG_COLOR)

    gs = fig.add_gridspec(
        3, 2,
        height_ratios=[0.12, 1, 1],
        hspace=0.35,
        wspace=0.25,
        left=0.05, right=0.97,
        top=0.97, bottom=0.04,
    )

    # ── Header panel ──────────────────────────────────────────────────────────
    ax_header = fig.add_subplot(gs[0, :])
    ax_header.set_facecolor(color)
    ax_header.set_xlim(0, 1)
    ax_header.set_ylim(0, 1)
    ax_header.axis("off")

    # Team name
    ax_header.text(
        0.02, 0.72, full_name,
        ha="left", va="center",
        fontsize=22, fontweight="bold", color="white",
        fontfamily=FONT_TITLE,
    )
    # Sub-header
    ax_header.text(
        0.02, 0.22, "2025 Defense Report  ·  Regular Season  ·  nflverse Data",
        ha="left", va="center",
        fontsize=9, color="rgba(255,255,255,0.75)",
        fontfamily=FONT_BODY,
    )

    # Headline stats from overview
    ov = overview[overview["defteam"] == team]
    if not ov.empty:
        row = ov.iloc[0]
        stats_text = []
        if not pd.isna(row.get("epa_allowed", np.nan)):
            stats_text.append(f"EPA/play {row['epa_allowed']:+.3f}")
        if not pd.isna(row.get("success_rate_allowed", np.nan)):
            stats_text.append(f"Success rate {row['success_rate_allowed']:.1%}")
        if not pd.isna(row.get("yards_allowed", np.nan)):
            stats_text.append(f"Yards/play {row['yards_allowed']:.1f}")
        if not pd.isna(row.get("epa_rank", np.nan)):
            stats_text.append(f"EPA rank #{int(row['epa_rank'])} of {int(row.get('total_teams', 32))}")
        stat_line = "  ·  ".join(stats_text)
        ax_header.text(
            0.98, 0.72, stat_line,
            ha="right", va="center",
            fontsize=10, color="white",
            fontfamily=FONT_BODY,
        )

    # ── 4 panels ──────────────────────────────────────────────────────────────
    ax_p1 = fig.add_subplot(gs[1, 0])
    ax_p2 = fig.add_subplot(gs[1, 1])
    ax_p3 = fig.add_subplot(gs[2, 0])
    ax_p4 = fig.add_subplot(gs[2, 1])

    panel_personnel(ax_p1, personnel,   team, color, league_avg)
    panel_front(    ax_p2, front,       team, color, league_avg)
    panel_game_script(ax_p3, game_script, team, color, league_avg)
    panel_redzone(  ax_p4, redzone,     team, color, league_avg)

    # Light background for data panels
    for ax in [ax_p1, ax_p2, ax_p3, ax_p4]:
        for spine in ax.spines.values():
            spine.set_edgecolor(GRID_COLOR)

    # ── Save ──────────────────────────────────────────────────────────────────
    out_path = ASSETS_DIR / f"{team}_defense_{YEAR}.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Saved: {out_path.name}")
    return out_path


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate defense infographic PNG(s).")
    parser.add_argument("--team", type=str, default=None,
                        help="Team code (e.g., KC, SF). Omit for all 32 teams.")
    parser.add_argument("--year", type=int, default=YEAR)
    args = parser.parse_args()

    # Check data files exist
    required = [
        "def_overview_2025.csv", "def_personnel_2025.csv",
        "def_front_2025.csv", "def_game_script_2025.csv",
        "def_redzone_2025.csv", "league_avg_2025.json",
    ]
    missing = [f for f in required if not (DATA_DIR / f).exists()]
    if missing:
        print(f"ERROR: Missing data files: {missing}")
        print("Run `python compute_defense_metrics.py` first.")
        return

    overview, personnel, front, game_script, redzone, league_avg = load_data()

    teams = [args.team.upper()] if args.team else sorted(TEAM_PRIMARY.keys())
    invalid = [t for t in teams if t not in TEAM_PRIMARY]
    if invalid:
        print(f"Unknown team codes: {invalid}")
        print(f"Valid codes: {sorted(TEAM_PRIMARY.keys())}")
        return

    print(f"Generating infographic(s) for {len(teams)} team(s) → {ASSETS_DIR}")
    for team in teams:
        generate(team, overview, personnel, front, game_script, redzone, league_avg)

    print(f"\nDone. {len(teams)} infographic(s) saved to {ASSETS_DIR}")


if __name__ == "__main__":
    main()
