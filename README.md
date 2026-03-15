# 🛡️ Does Your Team's Defense Actually Hold Up?

![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit&logoColor=white)
![Data: nflverse](https://img.shields.io/badge/Data-nflverse%202025-green)
![Season: 2025 NFL](https://img.shields.io/badge/Season-2025%20NFL%20Regular-orange)

**Part 2 of the 2026 NFL Analysis Series** · [Project 1 → The QB Report Card](../QB_Report_Card/)

Select any NFL team and see exactly how their 2025 defense held up — against every offensive formation, with the lead, from behind, and inside the red zone. Every team's fanbase is a distribution channel: *"Look how bad the [team] defense was against 11 personnel."*

> 📸 Screenshot coming soon — deploy to Streamlit Community Cloud and update this link.

---

## What It Analyzes

| Tab | What It Measures | Key Metric |
|-----|-----------------|------------|
| **Personnel Matchups** | How the defense fared against each offensive personnel package (11, 12, 21, 22, etc.) | EPA allowed + Success rate allowed |
| **Defensive Front** | Pass and run efficiency surrendered against light, standard, and heavy defensive box alignments | Yards allowed, YAC allowed, EPA |
| **Game Script** | 2nd-half defensive performance split by score situation (up big → down big) | EPA allowed per play |
| **Red Zone** | Inside-the-20 efficiency by pass-rush intensity (blitz vs. base) and down, with/without pressure. Headline stats shown as three gauge dials (TD Rate · EPA/Play · Success Rate) with green/yellow/red zones calibrated for defense performance. | TD rate, EPA allowed |

---

## How It Works — Data Pipeline

```
nflverse (GitHub releases)
    play_by_play_2025.parquet          ← base PBP (EPA, yards, success, etc.)
  + pbp_participation_2025.parquet     ← offense_personnel, defenders_in_box,
                                          number_of_pass_rushers
          │
          ▼  nfl_data_py.import_pbp_data([2025], include_participation=True)
          │
  compute_defense_metrics.py
          │  Filter: REG season · pass + run plays only
          │  Derive: personnel grouping, def_front, coverage_look,
          │          score_bucket (defense perspective), red_zone_flag
          │  Aggregate → 5 pre-built CSVs
          │
    data/
    ├── def_overview_2025.csv       ← headline stats (EPA rank, success rank)
    ├── def_personnel_2025.csv      ← Tab 1
    ├── def_front_2025.csv          ← Tab 2
    ├── def_game_script_2025.csv    ← Tab 3
    └── def_redzone_2025.csv        ← Tab 4
          │
          ▼
      streamlit run app.py          ← interactive team-selectable app
```

---

## Quick Start

### 1 — Clone and install

```bash
git clone <your-repo-url>
cd "NFLAnalProjects/Defense_Report"
pip install -r requirements.txt
```

> **Note:** `compute_defense_metrics.py` will auto-install any missing packages on first run.

### 2 — Build the data tables

```bash
python compute_defense_metrics.py
```

This downloads ~150–250 MB from nflverse on first run (cached locally at `data/raw_pbp_2025.parquet` for fast subsequent runs). Builds 5 aggregated CSVs and `league_avg_2025.json`.

To force a fresh download:

```bash
python compute_defense_metrics.py --force
```

### 3 — Launch the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Select any of the 32 NFL teams from the dropdown.

### 4 — Generate a shareable infographic (optional)

```bash
# Single team
python generate_infographic.py --team KC

# All 32 teams
python generate_infographic.py
```

Outputs `assets/{TEAM}_defense_2025.png` — a 14×18" PNG at 150 DPI, ready for social sharing.

---

## File Structure

```
Defense_Report/
├── compute_defense_metrics.py   # Data pipeline (run first)
├── app.py                       # Streamlit interactive app
├── generate_infographic.py      # Static PNG generator
├── requirements.txt
│
├── data/                        # Auto-populated by compute script
│   ├── raw_pbp_2025.parquet     # Local cache (avoids re-downloading)
│   ├── def_overview_2025.csv
│   ├── def_personnel_2025.csv
│   ├── def_front_2025.csv
│   ├── def_game_script_2025.csv
│   ├── def_redzone_2025.csv
│   └── league_avg_2025.json
│
└── assets/                      # Infographic PNGs
    └── {TEAM}_defense_2025.png
```

---

## 📊 Methodology

### Core Metrics

| Metric | Definition |
|--------|-----------|
| **EPA / play** | Expected Points Added per play allowed. Negative = defense performed better than expected. League average ≈ 0. |
| **Success Rate Allowed** | % of plays where the offense gained sufficient yards (1st down: 40%, 2nd: 60%, 3rd/4th: 100%). League avg ≈ 44%. |
| **Yards / play** | Average yards gained per pass or run play. |
| **YAC Allowed** | Yards after catch on completed passes — measures tackling and coverage depth after the reception. |
| **TD Rate** | Touchdowns per play in a given context (e.g., red zone). |

### Derived Dimensions

| Column | Source | Bucketing |
|--------|--------|-----------|
| `personnel_grouping` | `offense_personnel` (participation parquet) | 11 = 1 RB 1 TE 3 WR · 12 = 1 RB 2 TE 2 WR · 21 = 2 RB 1 TE 2 WR · etc. |
| `def_front` | `defenders_in_box` (participation parquet) | Light ≤5 · Standard 6 · Heavy 7 · Stacked 8+ |
| `coverage_look` | `number_of_pass_rushers` (participation parquet) | Light ≤3 · Base 4 · Blitz 5 · Heavy Blitz 6+ |
| `score_bucket` | `-score_differential` (defense's team perspective) | Down Big · Down · Slight Deficit · Tied · Slight Lead · Leading · Up Big |
| `red_zone_flag` | `yardline_100 ≤ 20` | Binary |
| `pressure_flag` | `qb_hit == 1 OR sack == 1` | Binary |

### Red Zone Gauge Chart

The three headline gauges (RZ TD Rate · RZ EPA / Play · RZ Success Rate) use color zones calibrated for a defense where **lower = better**:

| Zone | Color | TD Rate | EPA / Play | Success Rate |
|------|-------|---------|-----------|--------------|
| Elite | 🟢 Green | < 14% | < −0.07 | < 37% |
| Average | 🟡 Yellow | 14–24% | −0.07 to +0.07 | 37–47% |
| Poor | 🔴 Red | > 24% | > +0.07 | > 47% |

The dashed white line marks the **league average**. Delta values below each gauge show the difference vs. league, rounded to the nearest hundredth (e.g., `▼ 3.04%`), with green = better than league, red = worse.

### Minimum Play Threshold

Metric cells with fewer than **10 plays** are suppressed to prevent small-sample noise.

### Score Bucket Convention

Score buckets are framed from the **defensive team's perspective**: *"Up Big"* = your team leads by 14+, *"Down Big"* = your team trails by 14+. This makes the Game Script tab intuitive for fans.

---

## Requirements

```
streamlit>=1.32.0
pandas>=2.0.0
numpy>=1.26.0
plotly>=5.18.0
matplotlib>=3.8.0
nfl_data_py
pyarrow
```

---

## Data Source

Play-by-play and participation data from **[nflverse](https://github.com/nflverse/nflverse-data)** via the **[nfl_data_py](https://github.com/nflverse/nfl_data_py)** Python package.

- Base PBP: `play_by_play_2025.parquet` (nflfastR)
- Participation: `pbp_participation_2025.parquet` (nflverse)
- Season: 2025 NFL Regular Season

> Stats are not official NFL statistics. This project is for analytical and entertainment purposes.

---

## Part of the 2026 NFL Analysis Series

| # | Project | Description |
|---|---------|-------------|
| 1 | [The QB Report Card](../QB_Report_Card/) | Every starting QB graded across 5 situational dimensions |
| 2 | **Does Your Team's Defense Actually Hold Up?** | Team defense performance across personnel, front, game script, and red zone |
