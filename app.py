"""
Does Your Team's Defense Actually Hold Up? — 2025 NFL Season
Interactive Streamlit application

Run locally:
    streamlit run app.py

Deploy: push to GitHub → connect repo at share.streamlit.io
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Defense Report Card | 2025 NFL",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Constants ─────────────────────────────────────────────────────────────────
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

NAME_TO_CODE = {v: k for k, v in TEAM_NAMES.items()}
SORTED_NAMES = sorted(TEAM_NAMES.values())

# Neutral gray tones — readable on both light and dark
STEM_COLOR   = "rgba(130,140,160,0.45)"
GRID_COLOR   = "rgba(130,140,160,0.2)"
TICK_COLOR   = "rgba(155,168,190,1)"
AVG_COLOR    = "rgba(130,140,160,0.7)"
FONT_FAMILY  = "Source Sans 3, Helvetica Neue, Arial, sans-serif"


# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css(team_color: str = "#333333"):
    r, g, b = hex_to_rgb(team_color)
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&family=Source+Sans+3:ital,wght@0,300;0,400;0,600;0,700;1,400&display=swap');

        /* ═══════════════════════════════════════════════════
           THEME TOKENS — light defaults
           ═══════════════════════════════════════════════════ */
        :root {{
          --team-color:     {team_color};
          --team-r:         {r};
          --team-g:         {g};
          --team-b:         {b};

          --bg-app:         #FAFAF8;
          --bg-sidebar:     #F9FAFB;
          --bg-surface:     #FFFFFF;
          --bg-chip:        #F3F4F6;

          --txt-primary:    #111827;
          --txt-body:       #374151;
          --txt-muted:      #6B7280;
          --txt-faint:      #9CA3AF;

          --bdr-strong:     #1A1A1A;
          --bdr-mid:        #D1D5DB;
          --bdr-light:      #E5E7EB;

          --delta-pos:      #15803d;
          --delta-neg:      #b91c1c;
          --delta-neu:      #6B7280;
        }}

        /* ═══════════════════════════════════════════════════
           DARK MODE OVERRIDES
           ═══════════════════════════════════════════════════ */
        @media (prefers-color-scheme: dark) {{
          :root {{
            --bg-app:       #0E1117;
            --bg-sidebar:   #161C2D;
            --bg-surface:   #1C2333;
            --bg-chip:      #252D42;

            --txt-primary:  #F0F4FF;
            --txt-body:     #C8D4EC;
            --txt-muted:    #8899BB;
            --txt-faint:    #4D618A;

            --bdr-strong:   #E0E8FF;
            --bdr-mid:      #2D3D5A;
            --bdr-light:    #1A2540;

            --delta-pos:    #4ade80;
            --delta-neg:    #f87171;
            --delta-neu:    #64748b;
          }}
        }}

        /* ═══════════════════════════════════════════════════
           BASE RESETS
           ═══════════════════════════════════════════════════ */
        html, body, [class*="css"] {{
            font-family: 'Source Sans 3', 'Helvetica Neue', Arial, sans-serif;
        }}
        .main .block-container {{
            padding-top: 1.25rem;
            padding-left: 1.5rem;
            padding-right: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1300px;
        }}

        /* ═══════════════════════════════════════════════════
           HERO
           ═══════════════════════════════════════════════════ */
        .hero {{
            border-top: 4px solid var(--bdr-strong);
            border-bottom: 1px solid var(--bdr-mid);
            padding: 1.25rem 0 1rem;
            margin-bottom: 1.5rem;
        }}
        .hero-eyebrow {{
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--txt-muted);
            margin-bottom: 0.2rem;
        }}
        .hero-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: clamp(1.8rem, 4vw, 3rem);
            font-weight: 900;
            color: var(--txt-primary);
            line-height: 1.05;
            letter-spacing: -0.02em;
            margin-bottom: 0.35rem;
        }}
        .hero-sub {{
            font-size: 1.05rem;
            font-weight: 300;
            color: var(--txt-body);
            line-height: 1.55;
            max-width: 680px;
        }}

        /* ═══════════════════════════════════════════════════
           TEAM SELECTOR AREA
           ═══════════════════════════════════════════════════ */
        .selector-label {{
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--txt-muted);
            margin-bottom: 0.3rem;
        }}

        /* ═══════════════════════════════════════════════════
           TEAM BANNER — headline stats row
           ═══════════════════════════════════════════════════ */
        .team-banner {{
            border-left: 5px solid var(--team-color);
            padding: 0.9rem 1.25rem;
            background: rgba({r},{g},{b},0.06);
            border-radius: 0 8px 8px 0;
            margin-bottom: 1.5rem;
        }}
        .banner-team-name {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5rem;
            font-weight: 900;
            color: var(--txt-primary);
            margin-bottom: 0.75rem;
        }}
        .stat-chips-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }}
        .stat-chip {{
            flex: 1 1 140px;
            min-width: 120px;
            background: var(--bg-surface);
            border: 1px solid var(--bdr-mid);
            border-radius: 8px;
            padding: 0.6rem 0.9rem;
        }}
        .chip-label {{
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--txt-faint);
            margin-bottom: 0.15rem;
        }}
        .chip-value {{
            font-size: 1.35rem;
            font-weight: 900;
            font-family: 'Playfair Display', Georgia, serif;
            color: var(--txt-primary);
            line-height: 1.1;
        }}
        .chip-sub {{
            font-size: 0.7rem;
            color: var(--txt-muted);
            margin-top: 0.1rem;
        }}
        .chip-delta-pos {{ color: var(--delta-pos); font-weight: 600; }}
        .chip-delta-neg {{ color: var(--delta-neg); font-weight: 600; }}
        .chip-delta-neu {{ color: var(--delta-neu); }}

        /* ═══════════════════════════════════════════════════
           SECTION HEADERS
           ═══════════════════════════════════════════════════ */
        .section-head {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--txt-primary);
            border-bottom: 2px solid var(--bdr-strong);
            padding-bottom: 0.3rem;
            margin-bottom: 0.9rem;
        }}
        .chart-note {{
            font-size: 0.72rem;
            color: var(--txt-muted);
            font-style: italic;
            margin-top: -0.25rem;
            margin-bottom: 0.75rem;
        }}

        /* ═══════════════════════════════════════════════════
           SIDEBAR
           ═══════════════════════════════════════════════════ */
        [data-testid="stSidebar"] {{
            background: var(--bg-sidebar);
            border-right: 1px solid var(--bdr-light);
        }}
        .sidebar-head {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--txt-primary);
            margin-bottom: 0.25rem;
        }}
        .sidebar-note {{
            font-size: 0.74rem;
            color: var(--txt-muted);
            line-height: 1.65;
        }}

        /* ═══════════════════════════════════════════════════
           FOOTER
           ═══════════════════════════════════════════════════ */
        .footer-text {{
            margin-top: 2.5rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--bdr-light);
            font-size: 0.74rem;
            color: var(--txt-faint);
            text-align: center;
        }}
        .thin-hr {{
            border: none;
            border-top: 1px solid var(--bdr-light);
            margin: 1.5rem 0;
        }}

        /* ═══════════════════════════════════════════════════
           TABS — mobile friendly
           ═══════════════════════════════════════════════════ */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
            flex-wrap: wrap;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-family: 'Source Sans 3', sans-serif;
            font-size: 0.88rem;
            font-weight: 600;
            padding: 8px 14px;
            white-space: nowrap;
        }}

        /* ═══════════════════════════════════════════════════
           MOBILE — force columns to stack
           ═══════════════════════════════════════════════════ */
        @media (max-width: 640px) {{
            .main .block-container {{
                padding-left: 0.75rem;
                padding-right: 0.75rem;
            }}
            .hero-title {{
                font-size: 1.75rem;
            }}
            div[data-testid="stHorizontalBlock"] {{
                flex-direction: column;
            }}
            div[data-testid="stHorizontalBlock"] > div {{
                width: 100% !important;
                min-width: 100% !important;
                flex: 0 0 100% !important;
            }}
            .stTabs [data-baseweb="tab"] {{
                font-size: 0.78rem;
                padding: 6px 10px;
            }}
            .stat-chip {{
                flex: 1 1 100px;
                min-width: 100px;
            }}
        }}

        /* ═══════════════════════════════════════════════════
           CHROME HIDE
           ═══════════════════════════════════════════════════ */
        #MainMenu {{ visibility: hidden; }}
        footer     {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Data loading ──────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "data"


@st.cache_data
def load_overview() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "def_overview_2025.csv")


@st.cache_data
def load_personnel() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "def_personnel_2025.csv")


@st.cache_data
def load_front() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "def_front_2025.csv")


@st.cache_data
def load_game_script() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "def_game_script_2025.csv")


@st.cache_data
def load_redzone() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "def_redzone_2025.csv")


@st.cache_data
def load_league_avg() -> dict:
    path = DATA_DIR / "league_avg_2025.json"
    with open(path) as f:
        return json.load(f)


def _check_data_ready() -> bool:
    required = [
        "def_overview_2025.csv", "def_personnel_2025.csv",
        "def_front_2025.csv", "def_game_script_2025.csv",
        "def_redzone_2025.csv", "league_avg_2025.json",
    ]
    return all((DATA_DIR / f).exists() for f in required)


# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def team_color(code: str) -> str:
    return TEAM_PRIMARY.get(code, "#4B5563")


def _plotly_base(height: int = 360) -> dict:
    """Shared Plotly layout settings."""
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_FAMILY, size=12, color=TICK_COLOR),
        margin=dict(l=20, r=30, t=40, b=30),
        height=height,
        hoverlabel=dict(
            bgcolor="rgba(30,40,60,0.92)",
            bordercolor="rgba(120,140,180,0.3)",
            font=dict(family=FONT_FAMILY, size=12, color="#E8F0FF"),
        ),
    )


def _axis_style(title: str = "", **kwargs) -> dict:
    return dict(
        title=dict(text=title, font=dict(size=11, color=TICK_COLOR)),
        gridcolor=GRID_COLOR,
        linecolor=GRID_COLOR,
        tickfont=dict(size=11, color=TICK_COLOR),
        zeroline=False,
        **kwargs,
    )


# ── Chart builders ────────────────────────────────────────────────────────────

def lollipop_chart(
    df_chart: pd.DataFrame,
    x_col: str,
    y_col: str,
    color: str,
    title: str,
    x_title: str = "",
    avg_line: float | None = None,
    avg_label: str = "League Avg",
    x_format: str = ".3f",
    height: int = 360,
) -> go.Figure:
    """
    Horizontal lollipop chart.  df_chart must be sorted in display order already.
    x_col = numeric metric  |  y_col = category labels
    """
    df_chart = df_chart.dropna(subset=[x_col])
    if df_chart.empty:
        fig = go.Figure()
        fig.update_layout(**_plotly_base(height), title=title)
        return fig

    categories = df_chart[y_col].tolist()
    values     = df_chart[x_col].tolist()
    r, g, b    = hex_to_rgb(color)

    fig = go.Figure()

    # Stems — drawn as shapes so they sit behind the dots
    for cat, val in zip(categories, values):
        fig.add_shape(
            type="line",
            x0=0, x1=val, y0=cat, y1=cat,
            line=dict(color=STEM_COLOR, width=2),
            layer="below",
        )

    # Dots
    hover_text = [
        f"<b>{cat}</b><br>{x_title or x_col}: {val:{x_format}}"
        for cat, val in zip(categories, values)
    ]
    fig.add_trace(
        go.Scatter(
            x=values, y=categories,
            mode="markers",
            marker=dict(
                size=13, color=color,
                line=dict(width=2, color="rgba(255,255,255,0.80)"),
            ),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_text,
            showlegend=False,
        )
    )

    # League average vertical dashed line
    if avg_line is not None:
        fig.add_vline(
            x=avg_line,
            line_dash="dash",
            line_color=AVG_COLOR,
            line_width=1.5,
            annotation_text=avg_label,
            annotation_position="top right",
            annotation_font=dict(size=10, color=TICK_COLOR),
        )

    # Zero reference line (only if x range crosses zero)
    if any(v < 0 for v in values) or (avg_line is not None and avg_line < 0):
        fig.add_vline(x=0, line_color=GRID_COLOR, line_width=1)

    fig.update_layout(
        **_plotly_base(height),
        title=dict(text=title, font=dict(size=13, color=TICK_COLOR)),
        xaxis=_axis_style(x_title),
        yaxis=_axis_style(showgrid=False),
    )
    return fig


def grouped_bar_chart(
    df_chart: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    y_labels: list[str],
    colors: list[str],
    title: str,
    x_title: str = "",
    avg_lines: dict | None = None,
    height: int = 360,
    orientation: str = "h",
) -> go.Figure:
    """Grouped horizontal bar chart for multi-metric comparisons."""
    fig = go.Figure()
    for y_col, y_label, bar_color in zip(y_cols, y_labels, colors):
        if y_col not in df_chart.columns:
            continue
        sub = df_chart.dropna(subset=[y_col])
        if sub.empty:
            continue
        if orientation == "h":
            fig.add_trace(go.Bar(
                x=sub[y_col], y=sub[x_col],
                name=y_label,
                orientation="h",
                marker_color=bar_color,
                hovertemplate=f"<b>%{{y}}</b><br>{y_label}: %{{x:.3f}}<extra></extra>",
            ))
        else:
            fig.add_trace(go.Bar(
                x=sub[x_col], y=sub[y_col],
                name=y_label,
                marker_color=bar_color,
                hovertemplate=f"<b>%{{x}}</b><br>{y_label}: %{{y:.3f}}<extra></extra>",
            ))

    if avg_lines:
        for label, val in avg_lines.items():
            fig.add_vline(
                x=val, line_dash="dash", line_color=AVG_COLOR, line_width=1.2,
                annotation_text=label, annotation_position="top right",
                annotation_font=dict(size=9, color=TICK_COLOR),
            )

    fig.update_layout(
        **_plotly_base(height),
        title=dict(text=title, font=dict(size=13, color=TICK_COLOR)),
        barmode="group",
        xaxis=_axis_style(x_title),
        yaxis=_axis_style(showgrid=False),
        legend=dict(
            font=dict(size=11, family=FONT_FAMILY, color=TICK_COLOR),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ── Stat chip HTML ────────────────────────────────────────────────────────────

def stat_chip(label: str, value: str, sub: str = "", delta_cls: str = "chip-delta-neu") -> str:
    return f"""
    <div class="stat-chip">
      <div class="chip-label">{label}</div>
      <div class="chip-value">{value}</div>
      <div class="chip-sub {delta_cls}">{sub}</div>
    </div>
    """


# ── Tab builders ──────────────────────────────────────────────────────────────

def tab_personnel(df_personnel: pd.DataFrame, team: str, color: str, league_avg: dict):
    df_team = df_personnel[df_personnel["defteam"] == team].copy()
    if df_team.empty:
        st.info("No personnel data available for this team.")
        return

    # Sort by plays descending (most common packages first)
    df_team = df_team.sort_values("plays", ascending=False)

    # Build display labels: "11 (N plays)"
    df_team["label"] = (
        df_team["personnel_grouping"].astype(str) + "  (" +
        df_team["plays"].astype(int).astype(str) + " plays)"
    )

    st.markdown('<div class="section-head">Personnel Matchups</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-note">How did the defense hold up against each offensive personnel grouping?'
        ' Dashed line = league average. Longer bar = more allowed by the defense.</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        fig_epa = grouped_bar_chart(
            df_chart  = df_team,
            x_col     = "label",
            y_cols    = ["epa_allowed"],
            y_labels  = ["EPA / play"],
            colors    = [color],
            title     = "EPA Allowed per Play",
            x_title   = "EPA / play  (lower = better defense)",
            avg_lines = {"League": league_avg.get("epa_allowed")}
                        if league_avg.get("epa_allowed") is not None else None,
            height    = max(300, 50 * len(df_team) + 60),
        )
        st.plotly_chart(fig_epa, use_container_width=True, config={"responsive": True})

    with col_b:
        fig_sr = grouped_bar_chart(
            df_chart  = df_team,
            x_col     = "label",
            y_cols    = ["success_rate_allowed"],
            y_labels  = ["Success rate"],
            colors    = [color],
            title     = "Success Rate Allowed",
            x_title   = "Offensive success rate  (lower = better defense)",
            avg_lines = {"League": league_avg.get("success_rate")}
                        if league_avg.get("success_rate") is not None else None,
            height    = max(300, 50 * len(df_team) + 60),
        )
        fig_sr.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig_sr, use_container_width=True, config={"responsive": True})

    # YAC chart — below, full width
    df_yac = df_team.dropna(subset=["yac_allowed"])
    if not df_yac.empty:
        st.markdown('<hr class="thin-hr">', unsafe_allow_html=True)
        fig_yac = grouped_bar_chart(
            df_chart  = df_yac,
            x_col     = "label",
            y_cols    = ["yac_allowed"],
            y_labels  = ["Avg YAC / completion"],
            colors    = [color],
            title     = "Yards After Catch Allowed (pass plays only)",
            x_title   = "Avg YAC / completion  (lower = tighter coverage)",
            height    = max(280, 50 * len(df_yac) + 60),
        )
        st.plotly_chart(fig_yac, use_container_width=True, config={"responsive": True})

    with st.expander("What does this show?"):
        st.markdown(
            "**Personnel grouping** refers to the offensive personnel package: "
            "**11** = 1 RB, 1 TE, 3 WR (spread); **12** = 1 RB, 2 TE, 2 WR; "
            "**21** = 2 RB, 1 TE, 2 WR; etc.\n\n"
            "**EPA/play** — Expected Points Added per play allowed. Negative = defense doing its job. "
            "League average is close to 0.\n\n"
            "**Success rate** — % of plays where the offense gained ≥ 40/60/100% of yards needed "
            "on 1st/2nd/3rd-4th down (standard nflfastR definition). League avg ~44%.\n\n"
            "**YAC** — Yards After Catch on completions. High YAC allowed = soft coverage or missed tackles."
        )


def tab_front(df_front: pd.DataFrame, team: str, color: str):
    df_team = df_front[df_front["defteam"] == team].copy()
    if df_team.empty:
        st.info("No defensive front data available.")
        return

    df_pass = df_team[df_team["play_type"] == "pass"].copy()
    df_run  = df_team[df_team["play_type"] == "run"].copy()

    FRONT_ORDER = ["Light (≤5)", "Standard (6)", "Heavy (7)", "Stacked (8+)"]
    for d in [df_pass, df_run]:
        d["def_front"] = pd.Categorical(d["def_front"], categories=FRONT_ORDER, ordered=True)
        d.sort_values("def_front", inplace=True)

    r, g, b = hex_to_rgb(color)
    color2  = f"rgba({r},{g},{b},0.45)"

    st.markdown('<div class="section-head">Defensive Front</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-note">Defenders in the box — Light (≤5 DBs), Standard (6), '
        'Heavy (7), Stacked (8+).</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown("**Pass Defense by Front**")
        if not df_pass.empty:
            fig = grouped_bar_chart(
                df_chart  = df_pass,
                x_col     = "def_front",
                y_cols    = ["epa_allowed", "yac_allowed"],
                y_labels  = ["EPA / play", "YAC allowed"],
                colors    = [color, color2],
                title     = "",
                x_title   = "",
                height    = 340,
            )
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
        else:
            st.info("No pass play data.")

    with col_b:
        st.markdown("**Run Defense by Front**")
        if not df_run.empty:
            r2, g2, b2 = hex_to_rgb(color)
            fig = grouped_bar_chart(
                df_chart  = df_run,
                x_col     = "def_front",
                y_cols    = ["yards_allowed", "success_rate_allowed"],
                y_labels  = ["Yards / carry", "Success rate allowed"],
                colors    = [color, f"rgba({r2},{g2},{b2},0.45)"],
                title     = "",
                x_title   = "",
                height    = 340,
            )
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
        else:
            st.info("No run play data.")

    with st.expander("What does this show?"):
        st.markdown(
            "**Defenders in box (def_front)** is derived from `defenders_in_box`, "
            "the number of defenders lined up within ~1 yard of the line of scrimmage. "
            "More defenders in the box typically indicates a heavier run-defense look; "
            "fewer suggests a spread/nickel/dime coverage shell.\n\n"
            "**Pass Defense**: EPA per play and YAC allowed against each front. "
            "A light box with high YAC suggests the defense was in prevent-style coverage.\n\n"
            "**Run Defense**: Yards per carry and offensive success rate against each front."
        )


def tab_game_script(df_gs: pd.DataFrame, team: str, color: str, league_avg: dict):
    df_team = df_gs[df_gs["defteam"] == team].copy()
    if df_team.empty:
        st.info("No game script data available.")
        return

    SCORE_ORDER = ["Down Big", "Down (7-13)", "Slight Deficit", "Tied",
                   "Slight Lead", "Leading (7-13)", "Up Big"]

    # Aggregate Q3+Q4 together (combine qtrs)
    df_combined = (
        df_team
        .groupby("score_bucket", observed=True)
        .apply(lambda g: pd.Series({
            "plays":                int(g["plays"].sum()),
            "epa_allowed":          np.average(g["epa_allowed"].dropna(),
                                               weights=g.loc[g["epa_allowed"].notna(), "plays"])
                                    if g["epa_allowed"].notna().any() else np.nan,
            "success_rate_allowed": np.average(g["success_rate_allowed"].dropna(),
                                               weights=g.loc[g["success_rate_allowed"].notna(), "plays"])
                                    if g["success_rate_allowed"].notna().any() else np.nan,
        }))
        .reset_index()
    )
    df_combined["score_bucket"] = pd.Categorical(
        df_combined["score_bucket"], categories=SCORE_ORDER, ordered=True
    )
    df_combined = df_combined.sort_values("score_bucket")
    df_combined["label"] = (
        df_combined["score_bucket"].astype(str) + "  (" +
        df_combined["plays"].astype(str) + " plays)"
    )

    st.markdown('<div class="section-head">Game Script (2nd Half)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-note">How does the defense perform in the 2nd half depending on score? '
        'Left side = your team is losing. Right side = your team has the lead.</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        fig_epa = lollipop_chart(
            df_chart   = df_combined,
            x_col      = "epa_allowed",
            y_col      = "score_bucket",
            color      = color,
            title      = "EPA Allowed — 2nd Half",
            x_title    = "EPA / play  (lower = better defense)",
            avg_line   = league_avg.get("sh_epa"),
            avg_label  = "League (2H)",
            x_format   = ".3f",
            height     = 360,
        )
        st.plotly_chart(fig_epa, use_container_width=True, config={"responsive": True})

    with col_b:
        fig_sr = lollipop_chart(
            df_chart   = df_combined,
            x_col      = "success_rate_allowed",
            y_col      = "score_bucket",
            color      = color,
            title      = "Success Rate Allowed — 2nd Half",
            x_title    = "Offensive success rate  (lower = better defense)",
            avg_line   = league_avg.get("sh_success_rate"),
            avg_label  = "League (2H)",
            x_format   = ".1%",
            height     = 360,
        )
        fig_sr.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig_sr, use_container_width=True, config={"responsive": True})

    with st.expander("What does this show?"):
        st.markdown(
            "**Score buckets** represent your team's score margin at the time of the play "
            "(e.g., 'Up Big' = your team is leading by 14+). "
            "This view isolates 2nd-half plays (Q3 and Q4) to show how the defense "
            "manages games when it matters most.\n\n"
            "**The key question:** Does the defense clamp down when protecting a lead, "
            "or does it soften up and let opponents back in the game?"
        )


def tab_redzone(df_rz: pd.DataFrame, team: str, color: str, league_avg: dict):
    df_team = df_rz[df_rz["defteam"] == team].copy()
    if df_team.empty:
        st.info("No red zone data available.")
        return

    COVERAGE_ORDER = ["Light (≤3)", "Base (4)", "Blitz (5)", "Heavy Blitz (6+)"]
    DOWN_LABELS    = {1: "1st Down", 2: "2nd Down", 3: "3rd Down", 4: "4th Down"}

    # ── Headline RZ chips ─────────────────────────────────────────────────────
    rz_all = df_team.groupby("defteam", observed=True).apply(
        lambda g: pd.Series({
            "plays":     int(g["plays"].sum()),
            "td_rate":   np.average(g["td_rate"].dropna(),
                                    weights=g.loc[g["td_rate"].notna(), "plays"])
                         if g["td_rate"].notna().any() else np.nan,
            "epa":       np.average(g["epa_allowed"].dropna(),
                                    weights=g.loc[g["epa_allowed"].notna(), "plays"])
                         if g["epa_allowed"].notna().any() else np.nan,
            "sr":        np.average(g["success_rate_allowed"].dropna(),
                                    weights=g.loc[g["success_rate_allowed"].notna(), "plays"])
                         if g["success_rate_allowed"].notna().any() else np.nan,
        })
    ).reset_index()

    if not rz_all.empty:
        row       = rz_all.iloc[0]
        l_td      = league_avg.get("rz_td_rate", 0)
        l_epa     = league_avg.get("rz_epa", 0)
        l_sr      = league_avg.get("rz_success_rate", 0)
        td_val    = row["td_rate"]   if not pd.isna(row.get("td_rate",   np.nan)) else None
        epa_val   = row["epa"]       if not pd.isna(row.get("epa",       np.nan)) else None
        sr_val    = row["sr"]        if not pd.isna(row.get("sr",        np.nan)) else None

        def _delta_cls(val, avg, lower_is_better=True):
            if val is None or avg is None:
                return "chip-delta-neu"
            better = (val < avg) if lower_is_better else (val > avg)
            return "chip-delta-pos" if better else "chip-delta-neg"

        chips_html = '<div class="stat-chips-row">'
        if td_val is not None:
            d = td_val - l_td
            chips_html += stat_chip(
                "RZ TD Rate", f"{td_val:.1%}",
                f"{'▲' if d > 0 else '▼'} {abs(d):.1%} vs league",
                _delta_cls(td_val, l_td, lower_is_better=True),
            )
        if epa_val is not None:
            d = epa_val - l_epa
            chips_html += stat_chip(
                "RZ EPA / play", f"{epa_val:+.3f}",
                f"{'▲' if d > 0 else '▼'} {abs(d):.3f} vs league",
                _delta_cls(epa_val, l_epa, lower_is_better=True),
            )
        if sr_val is not None:
            d = sr_val - l_sr
            chips_html += stat_chip(
                "RZ Success Rate", f"{sr_val:.1%}",
                f"{'▲' if d > 0 else '▼'} {abs(d):.1%} vs league",
                _delta_cls(sr_val, l_sr, lower_is_better=True),
            )
        chips_html += "</div>"
        st.markdown(chips_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="section-head">Red Zone Efficiency</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-note">Inside the opponent 20-yard line. '
        'How often does the defense hold?</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2, gap="medium")

    # ── Chart A: TD rate by coverage look (lollipop) ──────────────────────────
    with col_a:
        df_cov = (
            df_team
            .groupby("coverage_look", observed=True)
            .apply(lambda g: pd.Series({
                "plays":   int(g["plays"].sum()),
                "td_rate": np.average(g["td_rate"].dropna(),
                                      weights=g.loc[g["td_rate"].notna(), "plays"])
                           if g["td_rate"].notna().any() else np.nan,
            }))
            .reset_index()
        )
        df_cov["coverage_look"] = pd.Categorical(
            df_cov["coverage_look"], categories=COVERAGE_ORDER, ordered=True
        )
        df_cov = df_cov.sort_values("coverage_look")
        df_cov["label"] = (
            df_cov["coverage_look"].astype(str) + "  (" +
            df_cov["plays"].astype(str) + " plays)"
        )

        fig_cov = lollipop_chart(
            df_chart   = df_cov,
            x_col      = "td_rate",
            y_col      = "label",
            color      = color,
            title      = "RZ TD Rate by Pass-Rush Look",
            x_title    = "Touchdown rate  (lower = better defense)",
            avg_line   = league_avg.get("rz_td_rate"),
            avg_label  = "League",
            x_format   = ".1%",
            height     = 340,
        )
        fig_cov.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig_cov, use_container_width=True, config={"responsive": True})

    # ── Chart B: TD rate by down × pressure (grouped bars) ───────────────────
    with col_b:
        df_down = (
            df_team[df_team["down"].isin([1, 2, 3, 4])]
            .groupby(["down", "pressure_flag"], observed=True)
            .apply(lambda g: pd.Series({
                "plays":   int(g["plays"].sum()),
                "td_rate": np.average(g["td_rate"].dropna(),
                                      weights=g.loc[g["td_rate"].notna(), "plays"])
                           if g["td_rate"].notna().any() else np.nan,
            }))
            .reset_index()
        )

        r_val, g_val, b_val = hex_to_rgb(color)
        fig_down = go.Figure()
        for pflag, label, bar_color in [
            (0, "No Pressure", color),
            (1, "Pressure (QB hit/sack)", f"rgba({r_val},{g_val},{b_val},0.45)"),
        ]:
            sub = df_down[df_down["pressure_flag"] == pflag]
            if sub.empty:
                continue
            sub["down_label"] = sub["down"].map(DOWN_LABELS)
            sub = sub.sort_values("down")
            fig_down.add_trace(go.Bar(
                x=sub["down_label"], y=sub["td_rate"],
                name=label,
                marker_color=bar_color,
                hovertemplate=(
                    "<b>%{x}</b><br>TD rate: %{y:.1%}<extra></extra>"
                ),
            ))

        fig_down.add_hline(
            y=league_avg.get("rz_td_rate", 0),
            line_dash="dash", line_color=AVG_COLOR,
            annotation_text="League Avg", annotation_position="bottom right",
            annotation_font=dict(size=9, color=TICK_COLOR),
        )
        fig_down.update_layout(
            **_plotly_base(340),
            title=dict(text="RZ TD Rate by Down & Pressure", font=dict(size=13, color=TICK_COLOR)),
            barmode="group",
            xaxis=_axis_style("Down"),
            yaxis=_axis_style("Touchdown rate", tickformat=".0%"),
            legend=dict(font=dict(size=11, family=FONT_FAMILY, color=TICK_COLOR),
                        bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_down, use_container_width=True, config={"responsive": True})

    with st.expander("What does this show?"):
        st.markdown(
            "**Pass-rush look** is derived from `number_of_pass_rushers`: "
            "Base (4 rushers), Blitz (5), Heavy Blitz (6+). "
            "Higher blitz rates in the red zone can force turnovers but also create coverage gaps.\n\n"
            "**Down & Pressure** shows red zone TD rate broken down by down number, "
            "separated by plays where the QB was hit or sacked vs clean pockets."
        )


# ── Main app ──────────────────────────────────────────────────────────────────

def main():
    # Check data is ready before injecting CSS (avoids rendering an empty page)
    if not _check_data_ready():
        st.error(
            "Data files not found. "
            "Run `python compute_defense_metrics.py` first to build the data tables."
        )
        st.stop()

    # Load data
    overview    = load_overview()
    personnel   = load_personnel()
    front       = load_front()
    game_script = load_game_script()
    redzone     = load_redzone()
    league_avg  = load_league_avg()

    # Default team = Kansas City Chiefs
    default_name = "Kansas City Chiefs"
    default_idx  = SORTED_NAMES.index(default_name) if default_name in SORTED_NAMES else 0

    # ── Team selector (top of page — visible on mobile) ───────────────────────
    # Inject placeholder CSS first (will be replaced after team selection)
    inject_css("#333333")

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero">
          <div class="hero-eyebrow">2025 NFL Season · Regular Season · nflverse Data</div>
          <div class="hero-title">Does Your Team's Defense Actually Hold Up?</div>
          <div class="hero-sub">
            Select your team and see exactly how the defense performed in 2025 —
            against every offensive formation, with the lead, from behind, and inside the red zone.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prominent team selector below hero
    st.markdown('<div class="selector-label">Select a team</div>', unsafe_allow_html=True)
    selected_name = st.selectbox(
        "Team",
        options=SORTED_NAMES,
        index=default_idx,
        label_visibility="collapsed",
    )
    selected_team = NAME_TO_CODE[selected_name]
    color         = team_color(selected_team)

    # Re-inject CSS with the actual team color now that we have it
    inject_css(color)

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-head">About This Tool</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="sidebar-note">
              <b>Data</b> — nflverse play-by-play + participation data, 2025 regular season<br><br>
              <b>EPA</b> — Expected Points Added per play. Negative = better for defense.<br><br>
              <b>Success Rate</b> — % of plays where the offense gained sufficient yards by down
              (1st: 40%, 2nd: 60%, 3rd/4th: 100%). League avg ~44%.<br><br>
              <b>Personnel groups</b> — derived from <code>offense_personnel</code>
              (nflverse participation data).<br>
              11 = 1 RB, 1 TE, 3 WR &nbsp;·&nbsp;
              12 = 1 RB, 2 TE, 2 WR &nbsp;·&nbsp;
              21 = 2 RB, 1 TE, 2 WR &nbsp;·&nbsp;
              22 = 2 RB, 2 TE, 1 WR<br><br>
              <b>Defenders in box</b> — from <code>defenders_in_box</code> (participation data).<br><br>
              <b>Minimum cell plays</b> — 10 plays required to display a metric; sparse cells hidden.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Headline stats banner ─────────────────────────────────────────────────
    ov = overview[overview["defteam"] == selected_team]
    if not ov.empty:
        row      = ov.iloc[0]
        n_teams  = int(row.get("total_teams", 32))
        epa_r    = int(row["epa_rank"])    if not pd.isna(row.get("epa_rank",    np.nan)) else "—"
        sr_r     = int(row["success_rank"]) if not pd.isna(row.get("success_rank", np.nan)) else "—"
        yds_r    = int(row["yards_rank"])   if not pd.isna(row.get("yards_rank",   np.nan)) else "—"
        epa_val  = row["epa_allowed"]
        sr_val   = row["success_rate_allowed"]
        yds_val  = row["yards_allowed"]

        def _rank_sub(rank, n, lower_better=True):
            if rank == "—":
                return "—"
            is_good = rank <= n // 4 if lower_better else rank >= (3 * n // 4)
            cls = "chip-delta-pos" if is_good else ("chip-delta-neg" if (rank > 3 * n // 4) else "chip-delta-neu")
            return f'<span class="{cls}">#{rank} of {n}</span>'

        l_epa = league_avg.get("epa_allowed", 0)
        l_sr  = league_avg.get("success_rate", 0)
        l_yds = league_avg.get("yards_allowed", 0)

        def _delta_sub(val, avg, lower_better=True, fmt=".3f"):
            if pd.isna(val):
                return ""
            d   = val - avg
            pos = d < 0 if lower_better else d > 0
            cls = "chip-delta-pos" if pos else "chip-delta-neg"
            sign = "▼" if d < 0 else "▲"
            return f'<span class="{cls}">{sign} {abs(d):{fmt}} vs league</span>'

        banner_chips = '<div class="stat-chips-row">'
        banner_chips += stat_chip(
            "EPA / Play",
            f"{epa_val:+.3f}" if not pd.isna(epa_val) else "—",
            _rank_sub(epa_r, n_teams) + " &nbsp;·&nbsp; " + _delta_sub(epa_val, l_epa),
        )
        banner_chips += stat_chip(
            "Success Rate Allowed",
            f"{sr_val:.1%}" if not pd.isna(sr_val) else "—",
            _rank_sub(sr_r, n_teams) + " &nbsp;·&nbsp; " + _delta_sub(sr_val, l_sr, fmt=".1%"),
        )
        banner_chips += stat_chip(
            "Yards / Play",
            f"{yds_val:.1f}" if not pd.isna(yds_val) else "—",
            _rank_sub(yds_r, n_teams) + " &nbsp;·&nbsp; " + _delta_sub(yds_val, l_yds, fmt=".2f"),
        )
        banner_chips += "</div>"

        r_val, g_val, b_val = hex_to_rgb(color)
        st.markdown(
            f"""
            <div class="team-banner">
              <div class="banner-team-name">{selected_name}</div>
              {banner_chips}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"No overview data found for {selected_name}.")

    # ── 4 Analysis Tabs ───────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "Personnel Matchups",
        "Defensive Front",
        "Game Script",
        "Red Zone",
    ])

    with tab1:
        tab_personnel(personnel, selected_team, color, league_avg)

    with tab2:
        tab_front(front, selected_team, color)

    with tab3:
        tab_game_script(game_script, selected_team, color, league_avg)

    with tab4:
        tab_redzone(redzone, selected_team, color, league_avg)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="footer-text">'
        "Built with nflverse data · 2025 NFL Regular Season · "
        "EPA and success rate are per-play averages · "
        "Minimum 10 plays to display a metric"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
