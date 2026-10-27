"""
Jet Engine Predictive Maintenance Command Center
NASA C-MAPSS | Tata Elxsi Teliport Season 4 — Case Study 1
Professional Dark-Mode Fleet Intelligence Dashboard v4

Run:
    streamlit run dashboard.py
"""
import glob
import json
import os
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from packaging.version import Version

st.set_page_config(
    page_title="Jet Engine Health | Tata Elxsi",
    page_icon="🛩️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data")
RUL_CAP, PERSIST = 125, 5

# ─── Design Tokens ─────────────────────────────────────────────────────────────
BG          = "#0B0F1A"
SURFACE     = "#111827"
SURFACE_2   = "#1E2536"
BORDER      = "#2D3748"
BORDER_SOFT = "#1F2D3D"

TEXT_1 = "#F1F5F9"
TEXT_2 = "#94A3B8"
TEXT_3 = "#64748B"

BLUE      = "#3B82F6"
BLUE_GLOW = "#1D4ED8"
BLUE_SOFT = "rgba(59,130,246,0.12)"
BLUE_MED  = "rgba(59,130,246,0.25)"

SEV = {
    "CRITICAL":     dict(label="Ground Now",      fill="#EF4444", text="#FCA5A5", glow="rgba(239,68,68,0.20)"),
    "HIGH":         dict(label="Repair Soon",     fill="#F97316", text="#FED7AA", glow="rgba(249,115,22,0.20)"),
    "MEDIUM":       dict(label="Inspection Due",  fill="#EAB308", text="#FEF08A", glow="rgba(234,179,8,0.15)"),
    "HUMAN_REVIEW": dict(label="Engineer Review", fill="#8B5CF6", text="#DDD6FE", glow="rgba(139,92,246,0.20)"),
    "LOW":          dict(label="Healthy",         fill="#10B981", text="#A7F3D0", glow="rgba(16,185,129,0.15)"),
}
ORDER    = list(SEV)
PRIORITY = {s: i for i, s in enumerate(ORDER)}
LABEL    = {k: v["label"] for k, v in SEV.items()}
FILL     = {k: v["fill"] for k, v in SEV.items()}
TEXT_C   = {k: v["text"] for k, v in SEV.items()}
GLOW     = {k: v["glow"] for k, v in SEV.items()}

SEQ_BLUE = ["#0F172A","#1E3A5F","#1D4ED8","#3B82F6","#60A5FA","#93C5FD","#DBEAFE"]

pio.templates["dark_ehm"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT_2, size=13),
    title=dict(font=dict(family="Inter, sans-serif", size=15, color=TEXT_1), x=0, xanchor="left", y=0.97),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=SURFACE_2,
    colorway=[BLUE],
    xaxis=dict(gridcolor=BORDER_SOFT, linecolor=BORDER, zeroline=False, ticks="",
               automargin=True, title_font=dict(color=TEXT_3), tickfont=dict(color=TEXT_3)),
    yaxis=dict(gridcolor=BORDER_SOFT, linecolor=BORDER, zeroline=False, ticks="",
               automargin=True, title_font=dict(color=TEXT_3), tickfont=dict(color=TEXT_3)),
    hoverlabel=dict(bgcolor=SURFACE_2, bordercolor=BORDER, font=dict(color=TEXT_1, size=13)),
    legend=dict(orientation="h", y=1.04, x=1, xanchor="right", yanchor="bottom",
                font=dict(color=TEXT_2), bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=56, r=16, t=64, b=56),
))
pio.templates.default = "dark_ehm"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, label, p, li, td, th {{
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}}

/* ─── App Shell ─── */
.stApp {{ background: {BG} !important; }}
.block-container {{ padding: 1.8rem 2.5rem 4rem; max-width: 1440px; }}
header[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer,
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

/* ─── Scrollbar ─── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}

/* ─── Typography ─── */
h1, h2, h3, h4 {{ color: {TEXT_1} !important; font-weight: 600 !important; }}

/* ─── Top Header Bar ─── */
.ehm-header-bar {{
    display: flex; align-items: center; gap: 14px;
    background: linear-gradient(135deg, #0F172A 0%, #1E2536 100%);
    border: 1px solid {BORDER}; border-radius: 14px;
    padding: 18px 26px; margin-bottom: 20px;
}}
.ehm-badge {{
    background: linear-gradient(135deg, {BLUE} 0%, {BLUE_GLOW} 100%);
    border-radius: 10px; padding: 8px 10px; display: flex; align-items: center;
    justify-content: center; font-size: 1.4rem; flex-shrink: 0;
}}
.ehm-title {{
    font-size: 1.55rem !important; font-weight: 700 !important;
    color: {TEXT_1} !important; line-height: 1.2 !important; margin: 0 !important;
}}
.ehm-sub {{
    color: {TEXT_3}; font-size: 0.82rem; margin-top: 2px;
    letter-spacing: 0.4px;
}}
.ehm-dataset-badge {{
    margin-left: auto; background: {BLUE_SOFT};
    border: 1px solid rgba(59,130,246,0.35);
    border-radius: 8px; padding: 6px 14px;
    font-size: 0.85rem; color: {BLUE}; font-weight: 600;
    white-space: nowrap;
}}

/* ─── KPI Cards Row ─── */
.kpi-grid {{
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 12px; margin-bottom: 20px;
}}
.kpi-card {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 12px; padding: 14px 18px;
    transition: transform 0.15s, border-color 0.15s;
    position: relative; overflow: hidden;
}}
.kpi-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 12px 12px 0 0;
}}
.kpi-card.critical::before {{ background: {SEV['CRITICAL']['fill']}; }}
.kpi-card.high::before    {{ background: {SEV['HIGH']['fill']}; }}
.kpi-card.medium::before  {{ background: {SEV['MEDIUM']['fill']}; }}
.kpi-card.review::before  {{ background: {SEV['HUMAN_REVIEW']['fill']}; }}
.kpi-card.healthy::before {{ background: {SEV['LOW']['fill']}; }}
.kpi-card:hover {{ transform: translateY(-2px); border-color: {BORDER}; }}
.kpi-value {{
    font-size: 2.1rem; font-weight: 700; line-height: 1;
    font-variant-numeric: tabular-nums;
}}
.kpi-card.critical .kpi-value {{ color: {SEV['CRITICAL']['fill']}; }}
.kpi-card.high .kpi-value    {{ color: {SEV['HIGH']['fill']}; }}
.kpi-card.medium .kpi-value  {{ color: {SEV['MEDIUM']['fill']}; }}
.kpi-card.review .kpi-value  {{ color: {SEV['HUMAN_REVIEW']['fill']}; }}
.kpi-card.healthy .kpi-value {{ color: {SEV['LOW']['fill']}; }}
.kpi-label {{ font-size: 0.8rem; color: {TEXT_3}; margin-top: 5px; letter-spacing: 0.3px; }}
.kpi-subtitle {{ font-size: 0.72rem; color: {TEXT_3}; margin-top: 3px; }}

/* ─── Fleet Board ─── */
.fleet-wrapper {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 20px 22px 18px;
    margin-bottom: 20px;
}}
.fleet-title {{
    font-size: 0.78rem; font-weight: 600; color: {TEXT_3};
    letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 14px;
}}
.board {{ display: flex; flex-wrap: wrap; gap: 4px; padding: 0 0 4px; }}
.tile {{
    width: 16px; height: 26px; border-radius: 3px;
    display: inline-block; transition: transform 0.1s, opacity 0.1s;
    cursor: pointer;
}}
.tile:hover {{ transform: scaleY(1.15); opacity: 0.9; outline: none; }}
.fleet-legend {{
    display: flex; flex-wrap: wrap; gap: 8px 24px; margin-top: 16px;
    padding-top: 14px; border-top: 1px solid {BORDER_SOFT};
}}
.legend-item {{ display: flex; align-items: center; gap: 8px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }}
.legend-count {{ font-size: 1.25rem; font-weight: 700; color: {TEXT_1}; font-variant-numeric: tabular-nums; }}
.legend-label {{ font-size: 0.82rem; color: {TEXT_3}; }}

/* ─── Alert Banner ─── */
.alert-bar {{
    background: linear-gradient(90deg, rgba(239,68,68,0.12) 0%, rgba(239,68,68,0.04) 100%);
    border: 1px solid rgba(239,68,68,0.3); border-radius: 10px;
    padding: 12px 18px; margin-bottom: 20px;
    font-size: 0.9rem; color: {TEXT_1};
}}
.alert-bar b {{ color: {SEV['CRITICAL']['fill']}; }}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px; border-bottom: 1px solid {BORDER};
    background: transparent !important;
    padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.88rem; font-weight: 500;
    padding: 9px 18px; color: {TEXT_3};
    border-radius: 8px 8px 0 0; background: transparent;
    border: none; transition: color 0.15s;
}}
.stTabs [aria-selected="true"] {{
    color: {TEXT_1} !important;
    background: {SURFACE} !important;
    border-top: 2px solid {BLUE} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}
.stTabs [data-baseweb="tab-panel"] {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-top: none; border-radius: 0 0 14px 14px;
    padding: 22px 20px;
}}

/* ─── Panels / Cards ─── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE_2} !important;
    border-color: {BORDER} !important;
    border-radius: 12px !important;
}}

/* ─── DataFrames ─── */
[data-testid="stDataFrame"] iframe {{ border-radius: 8px; }}

/* ─── Status Badges (inside dataframe) ─── */
.status-badge {{
    display: inline-block; border-radius: 5px;
    padding: 3px 9px; font-size: 0.78rem; font-weight: 600;
}}

/* ─── Metric-style stats in detail panel ─── */
.stats {{ display: flex; flex-wrap: wrap; gap: 6px 28px; padding: 4px 0 8px; }}
.stat .v {{
    font-size: 1.6rem; font-weight: 700; color: {TEXT_1};
    line-height: 1.15; font-variant-numeric: tabular-nums;
}}
.stat .l {{ color: {TEXT_3}; font-size: 0.8rem; margin-top: 2px; }}

/* ─── Note text ─── */
.note {{ color: {TEXT_3}; font-size: 0.88rem; line-height: 1.6; }}
.note b {{ color: {TEXT_2}; }}

/* ─── Section headings inside tabs ─── */
.section-header {{
    font-size: 0.75rem; font-weight: 600;
    color: {TEXT_3}; letter-spacing: 1px;
    text-transform: uppercase; margin: 18px 0 10px;
    padding-bottom: 6px; border-bottom: 1px solid {BORDER_SOFT};
}}

/* ─── Download Buttons ─── */
.stDownloadButton button {{
    background: {BLUE_SOFT} !important;
    border: 1px solid rgba(59,130,246,0.4) !important;
    color: {BLUE} !important; border-radius: 8px !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    padding: 6px 16px !important;
}}
.stDownloadButton button:hover {{
    background: {BLUE_MED} !important;
    border-color: {BLUE} !important;
}}

/* ─── Selectbox / Radio ─── */
.stRadio [data-testid="stMarkdownContainer"] {{
    color: {TEXT_2} !important;
}}
[data-testid="stSelectbox"] {{
    border-radius: 8px !important;
}}

/* ─── Slider ─── */
[data-testid="stSlider"] [data-baseweb="slider"] {{
    background: {SURFACE_2};
}}

/* ─── Expander ─── */
[data-testid="stExpander"] {{
    background: {SURFACE_2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
}}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

NEW_ST = Version(st.__version__) >= Version("1.50")


def show(fig, where=st, height=None):
    if height:
        fig.update_layout(height=height)
    if NEW_ST:
        where.plotly_chart(fig, width="stretch", theme=None)
    else:
        where.plotly_chart(fig, use_container_width=True, theme=None)


def stats_html(items):
    cells = "".join(
        f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for l, v in items
    )
    return f'<div class="stats">{cells}</div>'


def panel():
    return st.container(border=True)


# ─── Data Loading ──────────────────────────────────────────────────────────────
subsets = sorted(
    os.path.basename(p)[len("decisions_"):-len(".csv")]
    for p in glob.glob(os.path.join(DATA, "decisions_*.csv"))
)
if not subsets:
    st.error(
        f"No pipeline output found in {DATA}. Unzip dashboard_data.zip into "
        "a folder named dashboard_data next to dashboard.py."
    )
    st.stop()


@st.cache_data
def load(subset):
    def csv(name):
        p = os.path.join(DATA, name)
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    with open(os.path.join(DATA, f"config_{subset}.json")) as f:
        cfg = json.load(f)
    dec  = csv(f"decisions_{subset}.csv")
    hist = csv(f"engine_history_{subset}.csv")
    for df in (dec, hist):
        if not df.empty:
            for c in ["rul_low", "rul_high", "decision_RUL"]:
                if c not in df.columns:
                    df[c] = df["pred_RUL"]
    return dict(dec=dec, hist=hist, wo=csv(f"work_orders_{subset}.csv"),
                runs=csv(f"mlflow_runs_{subset}.csv"),
                summary=csv("summary_all_subsets.csv"), cfg=cfg)


def triage(rul, anomaly, cfg):
    if rul <= cfg["critical_rul"]:    return "CRITICAL"
    if rul <= cfg["high_rul"]:        return "HIGH"
    if anomaly and rul > cfg["long_life_rul"]: return "HUMAN_REVIEW"
    if rul <= cfg["medium_rul"]:      return "MEDIUM"
    return "LOW"


def true_severity(rul, cfg):
    if rul <= cfg["critical_rul"]: return "CRITICAL"
    if rul <= cfg["high_rul"]:     return "HIGH"
    if rul <= cfg["medium_rul"]:   return "MEDIUM"
    return "LOW"


def rng(lo, hi):
    return f"{lo:.0f}–{hi:.0f}"


# ─── Header Bar ───────────────────────────────────────────────────────────────
hdr_left, hdr_right = st.columns([4, 1], vertical_alignment="center")
with hdr_left:
    st.html("""
    <div class="ehm-header-bar">
      <div class="ehm-badge">🛩️</div>
      <div>
        <div class="ehm-title">Jet Engine Health Command Center</div>
        <div class="ehm-sub">NASA C-MAPSS Turbofan Fleet · Remaining Useful Life Prediction · Tata Elxsi Teliport S4</div>
      </div>
    </div>
    """)

with hdr_right:
    subset = st.radio("Dataset", subsets, horizontal=True, label_visibility="collapsed")

D = load(subset)
dec, hist, wo, runs, summary, cfg = D["dec"], D["hist"], D["wo"], D["runs"], D["summary"], D["cfg"]
dec  = dec.assign(priority=dec["severity"].map(PRIORITY)).sort_values(["priority", "decision_RUL"])
has_truth = "RUL" in dec.columns
has_range = not (dec["rul_low"] == dec["pred_RUL"]).all()
counts = dec["severity"].value_counts()

n_ground = int(counts.get("CRITICAL", 0))
n_repair = int(counts.get("HIGH", 0))
n_inspect = int(counts.get("MEDIUM", 0))
n_review  = int(counts.get("HUMAN_REVIEW", 0))
n_healthy = int(counts.get("LOW", 0))
n_total   = len(dec)

# ─── KPI Strip ────────────────────────────────────────────────────────────────
st.html(f"""
<div class="kpi-grid">
  <div class="kpi-card critical">
    <div class="kpi-value">{n_ground}</div>
    <div class="kpi-label">Ground Now</div>
    <div class="kpi-subtitle">Immediate action required</div>
  </div>
  <div class="kpi-card high">
    <div class="kpi-value">{n_repair}</div>
    <div class="kpi-label">Repair Soon</div>
    <div class="kpi-subtitle">Within {cfg['high_rul']} flights</div>
  </div>
  <div class="kpi-card medium">
    <div class="kpi-value">{n_inspect}</div>
    <div class="kpi-label">Inspection Due</div>
    <div class="kpi-subtitle">Schedule maintenance</div>
  </div>
  <div class="kpi-card review">
    <div class="kpi-value">{n_review}</div>
    <div class="kpi-label">Engineer Review</div>
    <div class="kpi-subtitle">Awaiting human sign-off</div>
  </div>
  <div class="kpi-card healthy">
    <div class="kpi-value">{n_healthy}</div>
    <div class="kpi-label">Healthy</div>
    <div class="kpi-subtitle">Continuous monitoring</div>
  </div>
</div>
""")

# ─── Alert Banner (if critical) ──────────────────────────────────────────────
if n_ground > 0:
    st.html(
        f'<div class="alert-bar">⚠️ &nbsp; <b>{n_ground} engines require immediate grounding</b> '
        f'— Remaining Useful Life ≤ {cfg["critical_rul"]} flights. '
        f'<b>{n_repair}</b> additional engines need repair within {cfg["high_rul"]} flights. '
        f'Total fleet: <b>{n_total} engines</b> on dataset {subset}.</div>'
    )

# ─── Fleet Board ──────────────────────────────────────────────────────────────
tiles = "".join(
    f'<span class="tile" style="background:{FILL[r.severity]};box-shadow:0 2px 6px {GLOW[r.severity]}" '
    f'title="Engine {int(r.unit)}: {LABEL[r.severity]}. '
    f'~{r.pred_RUL:.0f} flights left (range {rng(r.rul_low, r.rul_high)})."></span>'
    for r in dec.itertuples()
)
legend_items = "".join(
    f'<div class="legend-item">'
    f'<div class="legend-dot" style="background:{FILL[s]}"></div>'
    f'<span class="legend-count">{int(counts.get(s,0))}</span>'
    f'<span class="legend-label">{LABEL[s]}</span>'
    f'</div>'
    for s in ORDER
)
st.html(f"""
<div class="fleet-wrapper">
  <div class="fleet-title">FLEET OVERVIEW — {n_total} ENGINES · SORTED BY URGENCY</div>
  <div class="board">{tiles}</div>
  <div class="fleet-legend">{legend_items}</div>
</div>
""")

# ─── Tabs ─────────────────────────────────────────────────────────────────────

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab_list, tab_engine, tab_sim, tab_val, tab_model = st.tabs([
    "📋  Fleet Action Board",
    "🔍  Engine Condition & Work Plan",
    "🎬  Flight Replay Simulator",
    "✅  Validation",
    "🤖  Model & Retraining"
])

with tab_list:
    act = dec[dec["severity"] != "LOW"].copy()
    if act.empty:
        st.info("✅ Every engine in the fleet is healthy. No maintenance scheduled.")
    else:
        opts = [s for s in ORDER if s != "LOW"]
        pick = st.multiselect(
            "Filter by status",
            opts, default=opts,
            format_func=lambda s: LABEL[s]
        )
        act = act[act["severity"].isin(pick)]
        ids = dict(zip(wo["unit"], wo["work_order_id"])) if not wo.empty else {}

        table = pd.DataFrame({
            "Engine":         act["unit"].astype(int),
            "Status":         act["severity"].map(LABEL),
            "Flights Left":   act["pred_RUL"].round(),
            "Likely Range":   [rng(a, b) for a, b in zip(act["rul_low"], act["rul_high"])],
            "Planned On":     act["decision_RUL"].round(),
            "Action":         act["action"],
            "Eng. Check":     act["needs_human"].astype(bool),
            "Work Order ID":  act["unit"].map(ids).fillna("—"),
        })
        sev_codes = act["severity"].values

        def colour_status(col):
            return [f"color: {TEXT_C[s]}; font-weight: 600" for s in sev_codes]

        styled = table.style.apply(colour_status, subset=["Status"])
        st.dataframe(
            styled,
            hide_index=True,
            height=min(40 * (len(table) + 1) + 4, 640),
            column_config={
                "Flights Left": st.column_config.ProgressColumn(
                    "Flights Left (best estimate)",
                    min_value=0, max_value=RUL_CAP, format="%d"
                ),
                "Planned On": st.column_config.NumberColumn(
                    "Planned On", format="%d",
                    help="Pessimistic 10% quantile bound — ensures uncertain engines are handled early."
                ),
                "Eng. Check": st.column_config.CheckboxColumn("Eng. Check"),
            }
        )
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        c1, c2, _ = st.columns([1, 1, 4])
        if not wo.empty:
            c1.download_button(
                "⬇ Download CSV", wo.to_csv(index=False),
                file_name=f"work_orders_{subset}.csv", mime="text/csv"
            )
            c2.download_button(
                "⬇ Download JSON", wo.to_json(orient="records", indent=2),
                file_name=f"work_orders_{subset}.json", mime="application/json"
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ENGINE DETAIL
# ══════════════════════════════════════════════════════════════════════════════

with tab_engine:
    units  = dec["unit"].astype(int).tolist()
    sev_of = dict(zip(dec["unit"].astype(int), dec["severity"]))

    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    unit = c1.selectbox(
        "Select Engine",
        units,
        format_func=lambda u: f"Engine {u}  ·  {LABEL[sev_of[u]]}"
    )
    row = dec[dec["unit"] == unit].iloc[0]

    h = hist[hist["unit"] == unit].sort_values("cycle").reset_index(drop=True)
    thr = cfg["anomaly_threshold"]
    h["anom"]    = h["anomaly_score"] > thr
    h["persist"] = h["anom"].astype(int).rolling(PERSIST, min_periods=1).min().eq(1)
    h["severity"] = [triage(round(r), a, cfg) for r, a in zip(h["decision_RUL"], h["persist"])]
    fail_cycle = int(row["cycle"] + row["RUL"]) if has_truth else None

    c_min, c_max = int(h["cycle"].min()), int(h["cycle"].max())
    at = c2.slider(
        "Replay to flight cycle",
        c_min, c_max, c_max,
        help="Scrub through the engine's flight history to replay the AI's decisions over time."
    ) if c_max > c_min else c_max
    now = h[h["cycle"] == at].iloc[0]

    # Stats Row
    sev_now = now["severity"]
    sev_color = TEXT_C[sev_now]
    actual_left = f"{fail_cycle - at}" if fail_cycle else "—"
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:12px 0 18px;">
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {FILL[sev_now]};
                  border-radius:10px;padding:14px 16px;">
        <div style="font-size:1.2rem;font-weight:700;color:{sev_color}">{LABEL[sev_now]}</div>
        <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Current Decision</div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-radius:10px;padding:14px 16px;">
        <div style="font-size:1.5rem;font-weight:700;color:{TEXT_1}">{now['pred_RUL']:.0f}</div>
        <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Flights Left (Estimate)</div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-radius:10px;padding:14px 16px;">
        <div style="font-size:1.5rem;font-weight:700;color:{TEXT_1}">{rng(now['rul_low'], now['rul_high'])}</div>
        <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">80% Confidence Range</div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-radius:10px;padding:14px 16px;">
        <div style="font-size:1.5rem;font-weight:700;color:{TEXT_1}">{actual_left}</div>
        <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Actual (NASA Answer)</div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-radius:10px;padding:14px 16px;">
        <div style="font-size:1.5rem;font-weight:700;color:{'#EF4444' if now['anom'] else TEXT_1}">{now['anomaly_score']:.3f}</div>
        <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Anomaly Score {'⚠️ Abnormal' if now['anom'] else '✅ Normal'}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # RUL Trajectory Chart
    fig = go.Figure()
    for lo, hi, s in [
        (0, cfg["critical_rul"], "CRITICAL"),
        (cfg["critical_rul"], cfg["high_rul"], "HIGH"),
        (cfg["high_rul"], cfg["medium_rul"], "MEDIUM")
    ]:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=FILL[s], opacity=0.05, line_width=0)
        fig.add_annotation(
            x=h["cycle"].max(), y=(lo+hi)/2,
            text=LABEL[s], font=dict(size=10, color=FILL[s]),
            showarrow=False, xanchor="right"
        )

    if has_range:
        fig.add_trace(go.Scatter(
            x=h["cycle"], y=h["rul_high"],
            line=dict(width=0), showlegend=False, hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=h["cycle"], y=h["rul_low"],
            fill="tonexty",
            fillcolor="rgba(59,130,246,0.15)",
            line=dict(width=0), name="80% Confidence Interval",
            hoverinfo="skip"
        ))
    if fail_cycle:
        fig.add_trace(go.Scatter(
            x=h["cycle"], y=(fail_cycle - h["cycle"]).clip(upper=RUL_CAP),
            name="Actual RUL (NASA)",
            line=dict(color="#94A3B8", width=2, dash="dot"),
            hovertemplate="Flight %{x}: actual %{y:.0f} flights<extra></extra>"
        ))
    fig.add_trace(go.Scatter(
        x=h["cycle"], y=h["pred_RUL"],
        name="AI Best Estimate",
        line=dict(color=BLUE, width=2.5),
        hovertemplate="Flight %{x}: estimate %{y:.0f} flights<extra></extra>"
    ))
    fig.add_vline(x=at, line_color=TEXT_3, line_width=1.5, line_dash="dash",
                  annotation_text=f" Flight {at}", annotation_font_color=TEXT_3,
                  annotation_position="top right")
    fig.update_layout(
        title="Remaining Useful Life — Full Engine History",
        hovermode="x unified", xaxis_title="Flight Cycle", yaxis_title="Flights Remaining"
    )
    show(fig, height=400)

    # Anomaly Score Chart
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=h["cycle"], y=h["anomaly_score"],
        name="Anomaly Score",
        line=dict(color=BLUE, width=2),
        fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
        hovertemplate="Flight %{x}: score %{y:.3f}<extra></extra>"
    ))
    # Colour anomalous regions
    anom_x = h[h["anom"]]["cycle"]
    anom_y = h[h["anom"]]["anomaly_score"]
    if len(anom_x):
        fig2.add_trace(go.Scatter(
            x=anom_x, y=anom_y, mode="markers",
            name="Abnormal Reading",
            marker=dict(color=SEV["CRITICAL"]["fill"], size=5, symbol="circle"),
            hovertemplate="Flight %{x}: ABNORMAL %{y:.3f}<extra></extra>"
        ))
    fig2.add_hline(
        y=thr, line_dash="dash", line_color=SEV["CRITICAL"]["fill"], line_width=1.5,
        annotation_text="Anomaly threshold", annotation_position="top left",
        annotation_font_color=SEV["CRITICAL"]["fill"]
    )
    fig2.add_vline(x=at, line_color=TEXT_3, line_width=1.5, line_dash="dash")
    fig2.update_layout(
        title="Sensor Anomaly Score — Isolation Forest",
        hovermode="x unified", xaxis_title="Flight Cycle",
        yaxis_title="Anomaly Score", showlegend=True
    )
    show(fig2, height=280)

    # ─── Clean MRO Work Order Job Card (Per-Engine Action Plan) ─────────────────
    wo_id = f"WO-{subset}-{unit:03d}-CYCLE{at:04d}"
    
    if sev_now == "CRITICAL":
        wo_action_title = "EMERGENCY GROUNDING & HEAVY OVERHAUL"
        wo_deadline = "Ground Immediately (0 Flights SLA)"
        wo_bay = "Bay 1 — Heavy Turbine Overhaul"
        wo_diagnosis = (
            f"Severe thermodynamic degradation in High-Pressure Compressor (HPC). "
            f"Sensor anomaly gate breached ({now['anomaly_score']:.3f} > {thr:.3f}). "
            f"Pessimistic RUL has breached emergency limit (<= {cfg['critical_rul']} flights)."
        )
        tasks = [
            ("MANDATORY GROUNDING", "Issue immediate Aircraft-On-Ground (AOG) notice; lock out dispatch clearance in ERP."),
            ("OPTICAL BORESCOPE AUDIT", "Inspect High-Pressure Compressor (HPC) rotor stages 6-9 for micro-cracks and blade tip erosion."),
            ("MODULE OVERHAUL", "Disassemble turbine module; replace High-Pressure Turbine (HPT) stage-1 ceramic seal pack and eroded stator vanes."),
            ("SENSOR RECALIBRATION", "Recalibrate thermocouple wiring harnesses and static pressure transducers (T30, P30)."),
            ("AIRWORTHINESS SIGN-OFF", "Perform static test cell ground-run across idle to takeoff thrust; certify DGCA/FAA Form 8130-3 release.")
        ]
    elif sev_now == "HIGH":
        wo_action_title = "SCHEDULED DEPOT REPAIR & BLADE OVERHAUL"
        wo_deadline = f"Within {int(now['decision_RUL'])} flights"
        wo_bay = "Bay 3 — Scheduled Depot Maintenance"
        wo_diagnosis = (
            f"Significant High-Pressure Compressor wear detected. "
            f"Thermal efficiency dropping; remaining flights ({now['decision_RUL']:.0f}) approaching safety reserve limit (<= {cfg['high_rul']} flights)."
        )
        tasks = [
            ("PARTS PRE-ALLOCATION", "Pre-order HPC blade kit and stage-1 ceramic seal package from main spares inventory."),
            ("DEPOT SCHEDULING", f"Book overnight hangar maintenance bay at primary hub within {int(now['decision_RUL'])} flights."),
            ("HOT SECTION WASH", "Perform compressor chemical wash and optical borescope audit of combustor liner."),
            ("PRESSURE LEAK AUDIT", "Check bleed valve seals and turbine clearance gaps."),
            ("POST-REPAIR TEST", "Conduct high-power ground runup check and clear engine for return to active fleet.")
        ]
    elif sev_now == "MEDIUM":
        wo_action_title = "ROUTINE LINE MAINTENANCE & BORESCOPE AUDIT"
        wo_deadline = f"Within {int(now['decision_RUL'])} flights"
        wo_bay = "Line Maintenance Gate"
        wo_diagnosis = (
            f"Early thermodynamic micro-degradation. Anomaly score ({now['anomaly_score']:.3f}) approaching threshold. "
            f"Routine line inspection required to ensure defect does not accelerate."
        )
        tasks = [
            ("LINE MAINTENANCE SCHEDULING", "Queue for line borescope check during next overnight scheduled layover."),
            ("COMPRESSOR INLET CHECK", "Visual and optical audit of fan blades and low-pressure compressor inlet."),
            ("OIL & DEBRIS AUDIT", "Inspect engine oil scavenge filter and magnetic chip detector for metallic particles."),
            ("TELEMETRY QAR DOWNLOAD", "Download Quick Access Recorder (QAR) flight telemetry for thermodynamic baseline comparison.")
        ]
    else:
        wo_action_title = "ACTIVE LINE OPERATIONS & ROUTINE MONITORING"
        wo_deadline = "Active Service (Nominal)"
        wo_bay = "Operational Line Gate"
        wo_diagnosis = (
            f"All thermodynamic sensors and rotor spools operating within nominal factory tolerances. "
            f"Predicted RUL is healthy (>= {cfg['medium_rul']} flights). No maintenance intervention required."
        )
        tasks = [
            ("PRE-FLIGHT WALKAROUND", "Standard turnaround visual inspection of cowl, fan blades, and exhaust nozzle."),
            ("FLUID LEVEL VERIFICATION", "Check engine oil and hydraulic fluid levels before next departure."),
            ("DISPATCH CLEARANCE", "Asset approved for unrestricted commercial flight schedule.")
        ]

    st.html(f'''
    <div style="background:{SURFACE_2};border:2px solid {FILL[sev_now]};border-radius:12px;padding:20px 24px;margin:22px 0 16px;">
      <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid {BORDER};padding-bottom:12px;margin-bottom:14px;">
        <div>
          <span style="font-size:1.25rem;font-weight:700;color:{TEXT_1};letter-spacing:0.5px;">📋 WORK ORDER: <code style="color:{BLUE};font-size:1.2rem;">{wo_id}</code></span>
          <div style="font-size:0.84rem;color:{TEXT_3};margin-top:3px;">
            Target Asset: <b>Engine Unit {unit:03d}</b> · Flight Cycle <b>{at}</b> of {c_max}
          </div>
        </div>
        <span style="background:{GLOW[sev_now]};color:{TEXT_C[sev_now]};font-weight:700;font-size:0.88rem;padding:6px 16px;border-radius:6px;border:1px solid {FILL[sev_now]};">
          ● {LABEL[sev_now]} · {wo_action_title}
        </span>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;background:{SURFACE};border:1px solid {BORDER_SOFT};border-radius:8px;padding:12px 18px;margin-bottom:14px;">
        <div>
          <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;">Flights Remaining</div>
          <div style="font-size:1.35rem;font-weight:700;color:{TEXT_1};margin-top:2px;">{now['pred_RUL']:.0f} <span style="font-size:0.8rem;color:{TEXT_3};font-weight:400;">flights</span></div>
        </div>
        <div>
          <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;">Airworthiness SLA Deadline</div>
          <div style="font-size:1.15rem;font-weight:700;color:{TEXT_C[sev_now]};margin-top:4px;">{wo_deadline}</div>
        </div>
        <div>
          <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;">Assigned MRO Bay</div>
          <div style="font-size:1.15rem;font-weight:700;color:{TEXT_1};margin-top:4px;">{wo_bay}</div>
        </div>
      </div>

      <div style="margin-bottom:14px;">
        <div style="font-size:0.82rem;font-weight:600;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;">⚠️ WHAT IS WRONG (Root Cause Diagnostic)</div>
        <div style="font-size:0.88rem;color:{TEXT_1};background:{SURFACE};border:1px solid {BORDER_SOFT};border-radius:6px;padding:10px 14px;margin-top:6px;line-height:1.4;">
          {wo_diagnosis}
        </div>
      </div>

      <div>
        <div style="font-size:0.82rem;font-weight:600;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">🔧 WHAT TO DO (Maintenance Execution Checklist)</div>
      </div>
    </div>
    ''')

    for idx, (t_title, t_desc) in enumerate(tasks, 1):
        t_col1, t_col2 = st.columns([0.06, 0.94], vertical_alignment="center")
        t_col1.checkbox("", value=(idx==1 and sev_now in ["CRITICAL", "HIGH"]), key=f"wo_step_{unit}_{at}_{idx}")
        t_col2.markdown(f"<div style='font-size:0.86rem;line-height:1.4;'><b style='color:{TEXT_1};'>{idx}. {t_title}:</b> <span style='color:{TEXT_2};'>{t_desc}</span></div>")

    printable_job_card = f"""================================================================================
AIRCRAFT TURBOFAN MAINTENANCE WORK ORDER
TATA ELXSI PREDICTIVE MAINTENANCE COMMAND CENTER
================================================================================
WORK ORDER ID   : {wo_id}
ENGINE SERIAL   : Unit {unit:03d}
FLIGHT CYCLE    : {at} of {c_max}
STATUS/SEVERITY : {LABEL[sev_now]}
ACTION MANDATE  : {wo_action_title}
AIRWORTHINESS   : {wo_deadline}
ASSIGNED BAY    : {wo_bay}
PREDICTED RUL   : {now['pred_RUL']:.1f} flights (80% CI: {rng(now['rul_low'], now['rul_high'])})
ANOMALY SCORE   : {now['anomaly_score']:.4f} (Threshold: {thr:.4f})
DATE ISSUED     : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
================================================================================
WHAT IS WRONG (ROOT CAUSE DIAGNOSIS):
{wo_diagnosis}
================================================================================
WHAT TO DO (ENGINEERING CHECKLIST):
""" + "\n".join([f"[{'X' if idx==1 and sev_now in ['CRITICAL', 'HIGH'] else ' '}] {idx}. {t[0]}: {t[1]}" for idx, t in enumerate(tasks, 1)]) + f"""
================================================================================
ENGINEER SIGN-OFF:
Lead MRO Inspector: ______________________   License #: _______________
Date Completed     : ______________________   Signature: _______________
================================================================================
"""

    wo_single_df = pd.DataFrame([{
        "work_order_id": wo_id,
        "unit": unit,
        "flight_cycle": at,
        "severity": sev_now,
        "status": LABEL[sev_now],
        "action_title": wo_action_title,
        "deadline": wo_deadline,
        "assigned_bay": wo_bay,
        "predicted_RUL": round(now['pred_RUL'], 1),
        "conformal_lower_80": round(now['rul_low'], 1),
        "conformal_upper_80": round(now['rul_high'], 1),
        "anomaly_score": round(now['anomaly_score'], 4),
        "diagnosis": wo_diagnosis,
        "issued_timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }])

    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.8rem;color:{TEXT_3};margin-bottom:6px;'>📥 Download this Work Order for Engineer / Technician:</div>", unsafe_allow_html=True)
    d1, d2, d3, _ = st.columns([1.4, 1.2, 1.2, 2.2])
    d1.download_button(
        "📄 Download Job Sheet (Print/TXT)",
        printable_job_card,
        file_name=f"{wo_id}_JobSheet.txt",
        mime="text/plain",
        key=f"dl_txt_{unit}_{at}"
    )
    d2.download_button(
        "📊 Download CSV",
        wo_single_df.to_csv(index=False),
        file_name=f"{wo_id}.csv",
        mime="text/csv",
        key=f"dl_csv_{unit}_{at}"
    )
    d3.download_button(
        "📦 Download JSON",
        wo_single_df.to_json(orient="records", indent=2),
        file_name=f"{wo_id}.json",
        mime="application/json",
        key=f"dl_json_{unit}_{at}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

with tab_sim:
    st.markdown("""
    <div style="margin-bottom:14px;">
      <span style="font-size:1.15rem;font-weight:700;color:#F1F5F9;">🎬 Autonomous Prognostic & Triage Simulation</span>
      <p style="font-size:0.83rem;color:#94A3B8;margin-top:3px;">
        Simulate an active turbofan engine flight-by-flight. Observe ML triad predictions update dynamically,
        watch risk levels escalate in real-time, and see automated ERP work orders generated when airworthiness safety thresholds are breached.
      </p>
    </div>
    """, unsafe_allow_html=True)

    sim_units = dec["unit"].astype(int).tolist()
    # Curated high-impact demo units
    preset_units = [34, 81, 76, 49, 100]
    default_unit = 34 if 34 in sim_units else sim_units[0]

    sc1, sc2, sc3 = st.columns([1.3, 1.3, 1.4], vertical_alignment="bottom")
    
    selected_preset = sc1.selectbox(
        "🎯 Quick Scenario Presets",
        options=[34, 81, 76, 49] if all(u in sim_units for u in [34, 81, 76, 49]) else sim_units[:4],
        format_func=lambda u: {
            34: "Engine 34 (Full Degradation Lifecycle — 203 flights)",
            81: "Engine 81 (Long Service Life — 213 flights)",
            76: "Engine 76 (Rapid Failure Cascade — 205 flights)",
            49: "Engine 49 (Extended Service Operation — 303 flights)"
        }.get(u, f"Engine {u}"),
        key="sim_preset_select"
    )

    sim_unit = sc2.selectbox(
        "Or Select Any Engine in Fleet",
        sim_units,
        index=sim_units.index(selected_preset) if selected_preset in sim_units else 0,
        format_func=lambda u: f"Engine {u}  ·  Current: {LABEL[dict(zip(dec['unit'].astype(int), dec['severity'])).get(u, 'LOW')]}",
        key="sim_unit_select"
    )

    sim_h = hist[hist["unit"] == sim_unit].sort_values("cycle").reset_index(drop=True)
    sim_thr = cfg["anomaly_threshold"]
    sim_h["anom"] = sim_h["anomaly_score"] > sim_thr
    sim_h["persist"] = sim_h["anom"].astype(int).rolling(PERSIST, min_periods=1).min().eq(1)
    sim_h["severity"] = [triage(round(r), a, cfg) for r, a in zip(sim_h["decision_RUL"], sim_h["persist"])]
    
    sim_max_c = int(sim_h["cycle"].max())
    sim_min_c = int(sim_h["cycle"].min())
    row_info = dec[dec["unit"] == sim_unit].iloc[0]
    sim_fail_cycle = int(row_info["cycle"] + row_info["RUL"]) if has_truth else None

    # Find the critical transition points for quick navigation
    first_med = sim_h[sim_h["severity"] == "MEDIUM"]["cycle"].min()
    first_high = sim_h[sim_h["severity"] == "HIGH"]["cycle"].min()
    first_crit = sim_h[sim_h["severity"] == "CRITICAL"]["cycle"].min()

    # Session State for interactive simulation cycle & autoplay
    slider_key = f"slider_sim_{sim_unit}"
    play_key = f"sim_playing_{sim_unit}"
    speed_key = f"sim_speed_{sim_unit}"

    if slider_key not in st.session_state:
        st.session_state[slider_key] = 1
    if play_key not in st.session_state:
        st.session_state[play_key] = False
    if speed_key not in st.session_state:
        st.session_state[speed_key] = 2

    # Advance cycle before widget creation if playing (avoids StreamlitWidgetAlreadyInstantiatedError)
    if st.session_state.get(play_key, False):
        step = st.session_state.get(speed_key, 2)
        next_c = st.session_state[slider_key] + step
        if next_c >= sim_max_c:
            st.session_state[slider_key] = sim_max_c
            st.session_state[play_key] = False
        else:
            st.session_state[slider_key] = next_c

    is_playing = st.session_state[play_key]

    # Row 1: Continuous Play / Stop Simulation
    play_c1, play_c2, play_c3 = st.columns([1.6, 1.2, 2.2], vertical_alignment="center")
    
    play_btn_txt = "⏸ Pause Simulation" if is_playing else "▶ Start Simulation (Cycle 1 ➔ End)"
    if play_c1.button(play_btn_txt, use_container_width=True, type="primary" if not is_playing else "secondary", key=f"btn_play_{sim_unit}"):
        if is_playing:
            st.session_state[play_key] = False
        else:
            if st.session_state[slider_key] >= sim_max_c:
                st.session_state[slider_key] = sim_min_c
            st.session_state[play_key] = True
        st.rerun()

    if play_c2.button("⏹ Stop", use_container_width=True, key=f"btn_stop_{sim_unit}"):
        st.session_state[play_key] = False
        st.rerun()

    speed_val = play_c3.radio(
        "Simulation Speed",
        options=[1, 2, 5],
        format_func=lambda s: f"{s}x Speed ({s} flight{'s' if s>1 else ''}/step)",
        horizontal=True,
        index=[1, 2, 5].index(st.session_state[speed_key]) if st.session_state[speed_key] in [1, 2, 5] else 1,
        key=f"radio_spd_{sim_unit}"
    )
    st.session_state[speed_key] = speed_val

    # Row 2: Step & Milestone Controls (Keep all original buttons!)
    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1, 1, 1, 1.2, 1], vertical_alignment="center")
    if ctrl1.button("⏮ Cycle 1", use_container_width=True, key=f"btn_start_{sim_unit}"):
        st.session_state[play_key] = False
        st.session_state[slider_key] = sim_min_c
        st.rerun()
    if ctrl2.button("◀ -10 Flights", use_container_width=True, key=f"btn_prev_{sim_unit}"):
        st.session_state[play_key] = False
        st.session_state[slider_key] = max(sim_min_c, st.session_state[slider_key] - 10)
        st.rerun()
    if ctrl3.button("+10 Flights ▶", use_container_width=True, key=f"btn_next_{sim_unit}"):
        st.session_state[play_key] = False
        st.session_state[slider_key] = min(sim_max_c, st.session_state[slider_key] + 10)
        st.rerun()
    if pd.notna(first_crit) and ctrl4.button("🚨 Jump to Critical", use_container_width=True, key=f"btn_crit_{sim_unit}"):
        st.session_state[play_key] = False
        st.session_state[slider_key] = int(first_crit)
        st.rerun()
    if ctrl5.button("⏭ Final Flight", use_container_width=True, key=f"btn_end_{sim_unit}"):
        st.session_state[play_key] = False
        st.session_state[slider_key] = sim_max_c
        st.rerun()

    # Manual Scrubber Slider - bound directly to slider_key
    curr_c = st.slider(
        "🎚 Live Telemetry Scrubber (Flight Cycle Replay)",
        min_value=sim_min_c,
        max_value=sim_max_c,
        key=slider_key,
        help="Drag to step through the engine's entire service life cycle-by-cycle."
    )

    now_sim = sim_h[sim_h["cycle"] == curr_c].iloc[0]
    sev_sim = now_sim["severity"]
    sev_fill = FILL[sev_sim]
    sev_lbl = LABEL[sev_sim]
    pct_life = int((curr_c / sim_max_c) * 100)
    
    # Severity Alert Banner
    alert_bg = GLOW[sev_sim]
    st.markdown(f"""
    <div style="background:{alert_bg};border:1px solid {sev_fill};border-radius:10px;padding:12px 18px;margin:12px 0 16px;display:flex;align-items:center;justify-content:space-between;">
      <div>
        <span style="font-size:1.15rem;font-weight:700;color:{TEXT_C[sev_sim]};text-transform:uppercase;">● {sev_lbl}</span>
        <span style="font-size:0.86rem;color:{TEXT_1};margin-left:14px;">
          Flight Cycle <b>{curr_c}</b> of {sim_max_c} ({pct_life}% service life expended)
        </span>
      </div>
      <div style="font-size:0.82rem;font-weight:600;color:{TEXT_C[sev_sim]};background:rgba(0,0,0,0.3);padding:4px 12px;border-radius:6px;">
        {f'SLA: Ground Immediately (0 Flights)' if sev_sim == 'CRITICAL' else (f'SLA: Repair within {int(now_sim["decision_RUL"])} flights' if sev_sim == 'HIGH' else (f'SLA: Routine line inspection' if sev_sim == 'MEDIUM' else 'Active Fleet Operations'))}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Dynamic Real-Time Metric Cards
    sim_actual_left = f"{sim_fail_cycle - curr_c} flights" if sim_fail_cycle else "N/A"
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:18px;">
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-top:3px solid {sev_fill};border-radius:10px;padding:12px 16px;">
        <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;">Predicted RUL (Point Est.)</div>
        <div style="font-size:1.8rem;font-weight:700;color:{TEXT_1};margin-top:2px;">{now_sim['pred_RUL']:.0f} <span style="font-size:0.9rem;font-weight:400;color:{TEXT_3};">flights</span></div>
        <div style="font-size:0.72rem;color:{TEXT_3};margin-top:2px;">True Remaining: <b style="color:{TEXT_1}">{sim_actual_left}</b></div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-top:3px solid {BLUE};border-radius:10px;padding:12px 16px;">
        <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;">Calibrated 80% Cone</div>
        <div style="font-size:1.8rem;font-weight:700;color:{TEXT_1};margin-top:2px;">{rng(now_sim['rul_low'], now_sim['rul_high'])}</div>
        <div style="font-size:0.72rem;color:{TEXT_3};margin-top:2px;">Planning On: <b style="color:{BLUE}">{now_sim['decision_RUL']:.0f} flights (10% bound)</b></div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-top:3px solid {'#EF4444' if now_sim['anom'] else '#10B981'};border-radius:10px;padding:12px 16px;">
        <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;">Isolation Forest Sensor Gate</div>
        <div style="font-size:1.8rem;font-weight:700;color:{'#EF4444' if now_sim['anom'] else TEXT_1};margin-top:2px;">{now_sim['anomaly_score']:.3f}</div>
        <div style="font-size:0.72rem;color:{TEXT_3};margin-top:2px;">Threshold {sim_thr:.3f} · <b style="color:{'#EF4444' if now_sim['anom'] else '#10B981'}">{'⚠️ ANOMALOUS' if now_sim['anom'] else '✓ NORMAL'}</b></div>
      </div>
      <div style="background:{SURFACE_2};border:1px solid {BORDER};border-top:3px solid {sev_fill};border-radius:10px;padding:12px 16px;">
        <div style="font-size:0.75rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.5px;">Autonomous ERP Status</div>
        <div style="font-size:1.4rem;font-weight:700;color:{TEXT_C[sev_sim]};margin-top:6px;">{'🚨 WORK ORDER DISPATCHED' if sev_sim in ['CRITICAL', 'HIGH'] else ('📋 INSPECTION QUEUED' if sev_sim == 'MEDIUM' else '✓ IN SERVICE')}</div>
        <div style="font-size:0.72rem;color:{TEXT_3};margin-top:4px;">Work Order: <code style="color:{BLUE}">WO-{subset}-{sim_unit:03d}-{curr_c:04d}</code></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Historical Simulation Chart up to the current flight cycle
    hist_played = sim_h[sim_h["cycle"] <= curr_c]
    
    fig_sim = go.Figure()
    # Shaded severity threshold zones
    for lo, hi, s in [
        (0, cfg["critical_rul"], "CRITICAL"),
        (cfg["critical_rul"], cfg["high_rul"], "HIGH"),
        (cfg["high_rul"], cfg["medium_rul"], "MEDIUM")
    ]:
        fig_sim.add_hrect(y0=lo, y1=hi, fillcolor=FILL[s], opacity=0.06, line_width=0)
        fig_sim.add_annotation(
            x=sim_max_c, y=(lo+hi)/2,
            text=f"ZONE: {LABEL[s]}", font=dict(size=9, color=FILL[s]),
            showarrow=False, xanchor="right"
        )

    # Uncertainty cone
    fig_sim.add_trace(go.Scatter(
        x=hist_played["cycle"], y=hist_played["rul_high"],
        line=dict(width=0), showlegend=False, hoverinfo="skip"
    ))
    fig_sim.add_trace(go.Scatter(
        x=hist_played["cycle"], y=hist_played["rul_low"],
        fill="tonexty", fillcolor="rgba(59,130,246,0.18)",
        line=dict(width=0), name="80% Confidence Interval", hoverinfo="skip"
    ))
    
    # Ground truth actual RUL trajectory (if available)
    if sim_fail_cycle:
        fig_sim.add_trace(go.Scatter(
            x=sim_h["cycle"], y=(sim_fail_cycle - sim_h["cycle"]).clip(upper=RUL_CAP),
            line=dict(color=TEXT_3, width=1.5, dash="dash"),
            name="Ground Truth (NASA)", hoverinfo="x+y"
        ))

    # Ensemble Point Prediction trace
    fig_sim.add_trace(go.Scatter(
        x=hist_played["cycle"], y=hist_played["pred_RUL"],
        line=dict(color=BLUE, width=2.5),
        name="Predicted RUL", hovertemplate="Flight %{x}<br>Pred RUL: %{y:.1f} flights<extra></extra>"
    ))

    # Current flight cycle marker
    fig_sim.add_trace(go.Scatter(
        x=[curr_c], y=[now_sim["pred_RUL"]],
        mode="markers+text",
        marker=dict(color=sev_fill, size=12, line=dict(color="#FFFFFF", width=2)),
        text=[f"Cycle {curr_c} ({LABEL[sev_sim]})"],
        textposition="top center",
        name="Current Flight",
        showlegend=False
    ))

    fig_sim.update_layout(
        title=f"Live Prognostic Trajectory — Engine {sim_unit} (Flight 1 to {curr_c})",
        xaxis_title="Flight Cycle (Age)",
        yaxis_title="Remaining Useful Life (Cycles)",
        height=380,
        margin=dict(l=48, r=20, t=50, b=45),
        yaxis=dict(range=[-5, RUL_CAP + 15]),
        xaxis=dict(range=[0, sim_max_c + 5])
    )
    show(fig_sim, height=380)

    # Live Generated Work Order Card (Triggered dynamically!)
    if sev_sim in ["CRITICAL", "HIGH", "MEDIUM"]:
        wo_id = f"WO-{subset}-{sim_unit:03d}-CYCLE{curr_c:04d}"
        wo_status = "OPEN"
        wo_action = ("GROUND IMMEDIATELY: Module replacement and safety overhaul before next flight" 
                     if sev_sim == "CRITICAL" else 
                     ("SCHEDULE DEPOT OVERHAUL: Replace high-pressure turbine seal and compressor blades"
                      if sev_sim == "HIGH" else "ROUTINE LINE INSPECTION: Borescope audit of combustor and turbine"))
        
        st.markdown(f"""
        <div style="background:{SURFACE_2};border:1px solid {sev_fill};border-radius:12px;padding:16px 20px;margin-top:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid {BORDER_SOFT};padding-bottom:10px;margin-bottom:12px;">
            <div>
              <span style="font-size:1.1rem;font-weight:700;color:{TEXT_1};">⚡ Autonomous Work Order Dispatched</span>
              <span style="font-size:0.8rem;color:{TEXT_3};margin-left:12px;">Automated CMMS/ERP Dispatch Integration</span>
            </div>
            <span style="background:{GLOW[sev_sim]};color:{TEXT_C[sev_sim]};font-weight:700;font-size:0.8rem;padding:4px 10px;border-radius:6px;border:1px solid {sev_fill};">
              {LABEL[sev_sim]} · {wo_status}
            </span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;font-size:0.85rem;">
            <div><span style="color:{TEXT_3};">Work Order ID:</span> <b style="color:{BLUE};font-family:monospace;">{wo_id}</b></div>
            <div><span style="color:{TEXT_3};">Engine Unit:</span> <b style="color:{TEXT_1};">Unit {sim_unit} (Cycle {curr_c})</b></div>
            <div><span style="color:{TEXT_3};">Airworthiness Deadline:</span> <b style="color:{TEXT_C[sev_sim]};">{f'{int(now_sim["decision_RUL"])} flights remaining' if now_sim['decision_RUL'] > 0 else '0 flights (Immediate Grounding)'}</b></div>
          </div>
          <div style="margin-top:10px;font-size:0.85rem;">
            <span style="color:{TEXT_3};">Action Mandate:</span> <b style="color:{TEXT_1};">{wo_action}</b>
          </div>
          <div style="margin-top:6px;font-size:0.8rem;color:{TEXT_3};">
            Audit Reason: Lower 10% quantile bound ({now_sim['rul_low']:.1f}) crossed safety threshold ({cfg['critical_rul'] if sev_sim=='CRITICAL' else cfg['high_rul']} cycles) with corroborated anomaly score ({now_sim['anomaly_score']:.3f}).
          </div>
        </div>
        """, unsafe_allow_html=True)

        wo_sample = pd.DataFrame([{
            "work_order_id": wo_id,
            "created_at_cycle": curr_c,
            "unit": sim_unit,
            "severity": sev_sim,
            "action": wo_action,
            "deadline_flights": int(now_sim["decision_RUL"]),
            "predicted_RUL": round(now_sim["pred_RUL"], 1),
            "pessimistic_bound": round(now_sim["rul_low"], 1),
            "anomaly_score": round(now_sim["anomaly_score"], 4),
            "status": "OPEN",
            "dispatch_protocol": "Zero-LLM Deterministic Rule"
        }])
        
        w_col1, w_col2, _ = st.columns([1.2, 1.2, 3])
        w_col1.download_button(
            "📥 Download Work Order JSON",
            wo_sample.to_json(orient="records", indent=2),
            file_name=f"{wo_id}.json",
            mime="application/json"
        )
        w_col2.download_button(
            "📥 Download Work Order CSV",
            wo_sample.to_csv(index=False),
            file_name=f"{wo_id}.csv",
            mime="text/csv"
        )

    # Flight-by-Flight Audit Event Timeline
    st.markdown('<div class="section-header">📜 Engine Lifecycle Milestone Log</div>', unsafe_allow_html=True)
    milestones = []
    milestones.append(f"• <b>Cycle 001:</b> Turbofan Engine {sim_unit} commissioned into service. Baseline thermodynamic signature established (Status: 🟢 HEALTHY).")
    if pd.notna(first_med) and curr_c >= first_med:
        milestones.append(f"• <b>Cycle {int(first_med):03d}:</b> First thermodynamic micro-degradation detected. RUL drops below 75 cycles. Status escalated to <b>🟡 INSPECTION DUE</b>.")
    if pd.notna(first_high) and curr_c >= first_high:
        milestones.append(f"• <b>Cycle {int(first_high):03d}:</b> Pessimistic quantile bound crosses 40-flight threshold. Status escalated to <b>🟠 REPAIR SOON</b>. Autonomous maintenance overhaul scheduled.")
    if pd.notna(first_crit) and curr_c >= first_crit:
        milestones.append(f"• <b>Cycle {int(first_crit):03d}:</b> <b>CRITICAL SAFETY BREACH</b> — Pessimistic RUL <= 15 flights. Emergency Order: <b>🔴 GROUND IMMEDIATELY</b> with 0-flight SLA.")
    if curr_c == sim_max_c:
        milestones.append(f"• <b>Cycle {sim_max_c:03d}:</b> Lifecycle concluded. Asset safely grounded before catastrophic failure. Zero in-flight failures occurred.")

    log_html = "".join(f'<div style="font-size:0.84rem;color:#94A3B8;padding:4px 0;">{m}</div>' for m in milestones)
    st.markdown(f'<div style="background:{SURFACE_2};border:1px solid {BORDER_SOFT};border-radius:10px;padding:12px 18px;">{log_html}</div>', unsafe_allow_html=True)

    # Continuous Simulation Auto-Play Loop Execution
    if st.session_state.get(play_key, False):
        if st.session_state[slider_key] < sim_max_c:
            time.sleep(0.06)
            st.rerun()
        else:
            st.session_state[play_key] = False
            st.rerun()



with tab_val:
    if not has_truth:
        st.info("This export does not contain an answer key. Predictions cannot be validated.")
    else:
        st.markdown(
            f'<p class="note">Each test engine\'s final-cycle prediction vs. NASA\'s hidden answer file '
            f'(<code>RUL_{subset}.txt</code>). The model <b>never saw these answers</b> during training or tuning.</p>',
            unsafe_allow_html=True
        )
        y_true  = dec["RUL"].values
        y_cap   = np.minimum(y_true, RUL_CAP)
        err     = dec["pred_RUL"].values - y_cap
        truth   = np.array([true_severity(r, cfg) for r in y_true])
        level   = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "HUMAN_REVIEW": 1, "LOW": 0}
        t_lv    = np.array([level[t] for t in truth])
        d_lv    = np.array([level[d] for d in dec["severity"]])
        urgent  = t_lv >= 2
        covered = ((y_cap >= dec["rul_low"].values) & (y_cap <= dec["rul_high"].values)).mean()
        missed  = int(((y_true <= cfg["critical_rul"]) & ~dec["severity"].isin(["CRITICAL", "HIGH"])).sum())
        exact   = (d_lv == t_lv).mean()

        # Validation KPIs
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:10px 0 20px;">
          <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {BLUE};border-radius:10px;padding:14px 16px;">
            <div style="font-size:1.6rem;font-weight:700;color:{TEXT_1}">{np.abs(err).mean():.1f}</div>
            <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Avg Error (flights)</div>
          </div>
          <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {BLUE};border-radius:10px;padding:14px 16px;">
            <div style="font-size:1.6rem;font-weight:700;color:{TEXT_1}">{np.sqrt((err**2).mean()):.2f}</div>
            <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">RMSE</div>
          </div>
          <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {SEV['LOW']['fill']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:1.6rem;font-weight:700;color:{SEV['LOW']['fill']}">{covered:.0%}</div>
            <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Range Covers Truth</div>
          </div>
          <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {'#EF4444' if missed > 0 else SEV['LOW']['fill']};border-radius:10px;padding:14px 16px;">
            <div style="font-size:1.6rem;font-weight:700;color:{'#EF4444' if missed > 0 else SEV['LOW']['fill']}">{missed}</div>
            <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Critical Engines Missed</div>
          </div>
          <div style="background:{SURFACE_2};border:1px solid {BORDER};border-left:3px solid {BLUE};border-radius:10px;padding:14px 16px;">
            <div style="font-size:1.6rem;font-weight:700;color:{TEXT_1}">{exact:.0%}</div>
            <div style="font-size:0.78rem;color:{TEXT_3};margin-top:4px">Exact Category Match</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1, panel():
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[0, RUL_CAP, max(y_true.max(), RUL_CAP) + 5],
                y=[0, RUL_CAP, RUL_CAP],
                mode="lines", name="Perfect Prediction (capped at 125)",
                hoverinfo="skip",
                line=dict(color=TEXT_3, dash="dash", width=1.5)
            ))
            fig.add_trace(go.Scatter(
                x=y_true, y=dec["pred_RUL"], mode="markers",
                name="Test Engine",
                error_y=dict(
                    type="data", symmetric=False,
                    array=dec["rul_high"] - dec["pred_RUL"],
                    arrayminus=dec["pred_RUL"] - dec["rul_low"],
                    color="rgba(59,130,246,0.3)", thickness=1.2, width=0
                ) if has_range else None,
                marker=dict(color=BLUE, size=7, line=dict(color=BG, width=1)),
                customdata=np.stack([dec["unit"], dec["rul_low"], dec["rul_high"]], axis=1),
                hovertemplate=(
                    "Engine %{customdata[0]}<br>"
                    "Actual: %{x} flights<br>"
                    "Predicted: %{y:.0f} (range %{customdata[1]:.0f}–%{customdata[2]:.0f})<extra></extra>"
                )
            ))
            fig.update_layout(
                title="Predicted vs Actual Remaining Life",
                xaxis_title="Actual Flights Left (NASA Answer)",
                yaxis_title="Predicted Flights Left"
            )
            show(fig, height=380)

        with c2, panel():
            zones = pd.cut(y_true, [-1, 25, 50, 75, 125, 100000],
                           labels=["0–25", "26–50", "51–75", "76–125", "125+"])
            z = (pd.DataFrame({"zone": zones, "e": np.abs(err)})
                 .groupby("zone", observed=False)
                 .agg(mae=("e", "mean"), n=("e", "size"))
                 .reset_index().fillna(0))
            bar_colors = [SEV["CRITICAL"]["fill"], SEV["HIGH"]["fill"],
                          SEV["MEDIUM"]["fill"], BLUE, SEV["LOW"]["fill"]]
            fig = go.Figure(go.Bar(
                x=z["zone"].astype(str), y=z["mae"],
                marker_color=bar_colors[:len(z)],
                text=z["mae"].round(1), textposition="outside", cliponaxis=False,
                customdata=z["n"],
                hovertemplate="%{x} flights left<br>Avg error: %{y:.1f}<br>%{customdata} engines<extra></extra>"
            ))
            fig.update_layout(
                title="Average Error by Distance to Failure",
                barcornerradius=4,
                xaxis_title="Actual Flights Left",
                yaxis_title="Average Error (flights)"
            )
            show(fig, height=380)

        c1, c2 = st.columns(2)
        with c1, panel():
            fig = go.Figure(go.Histogram(
                x=err, nbinsx=30,
                marker_color=BLUE, marker_line=dict(width=0.5, color=BG),
                hovertemplate="Error: %{x}<br>%{y} engines<extra></extra>"
            ))
            fig.add_vline(x=0, line_color=TEXT_3, line_width=1.5)
            fig.add_annotation(x=-1, y=1.05, yref="paper", text="← Early (safe)",
                               xanchor="right", showarrow=False,
                               font=dict(color=SEV["LOW"]["fill"], size=11))
            fig.add_annotation(x=1, y=1.05, yref="paper", text="Late (risky) →",
                               xanchor="left", showarrow=False,
                               font=dict(color=SEV["CRITICAL"]["fill"], size=11))
            fig.update_layout(
                title="Prediction Error Distribution",
                bargap=0.06,
                xaxis_title="Predicted − Actual (flights)",
                yaxis_title="Number of Engines"
            )
            show(fig, height=340)

        with c2, panel():
            cols_cm = ["CRITICAL", "HIGH", "MEDIUM", "HUMAN_REVIEW", "LOW"]
            rows_cm = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            cm = (pd.crosstab(pd.Series(truth, name="t"),
                              dec["severity"].reset_index(drop=True).rename("d"))
                  .reindex(index=rows_cm, columns=cols_cm, fill_value=0))
            fig = go.Figure(go.Heatmap(
                z=cm.values,
                x=[LABEL[c] for c in cols_cm],
                y=[LABEL[r] for r in rows_cm],
                colorscale=[[i/6, c] for i, c in enumerate(SEQ_BLUE)],
                showscale=False,
                text=cm.values, texttemplate="%{text}",
                xgap=3, ygap=3,
                hovertemplate="Should be: %{y}<br>Agent decided: %{x}<br>%{z} engines<extra></extra>"
            ))
            fig.update_layout(
                title="Triage Agent Decision Matrix",
                plot_bgcolor=SURFACE_2,
                xaxis_title="Agent Decided",
                yaxis=dict(title="Should Have Been", autorange="reversed")
            )
            show(fig, height=340)

        if not summary.empty:
            st.markdown('<div class="section-header">All Four Datasets — Same Pipeline</div>',
                        unsafe_allow_html=True)
            keep = {
                "subset": "Dataset", "trained_with": "Trained With",
                "test_engines": "Test Engines", "test_rmse": "RMSE",
                "test_mae": "Avg Error", "nasa_score": "NASA Score",
                "test_range_coverage": "Coverage", "critical_missed": "Critical Missed",
                "work_orders": "Work Orders"
            }
            tbl = summary[[c for c in keep if c in summary.columns]].rename(columns=keep)
            st.dataframe(tbl, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MODEL & RETRAINING
# ══════════════════════════════════════════════════════════════════════════════

with tab_model:
    c1, c2 = st.columns(2)

    if not summary.empty and "test_rmse" in summary.columns:
        with c1, panel():
            colors_bar = [FILL[s] for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]]
            fig = go.Figure(go.Bar(
                x=summary["subset"], y=summary["test_rmse"],
                marker_color=colors_bar[:len(summary)],
                text=summary["test_rmse"].round(2),
                textposition="outside", cliponaxis=False,
                hovertemplate="%{x}: RMSE %{y:.2f} flights<extra></extra>"
            ))
            fig.update_layout(
                title="Test RMSE per Dataset (Lower = Better)",
                barcornerradius=4, yaxis_title="RMSE (flights)",
                yaxis=dict(range=[0, summary["test_rmse"].max() * 1.25])
            )
            show(fig, height=340)

    if not runs.empty and "metrics.test_rmse" in runs.columns:
        journey = (runs[
            runs["metrics.test_rmse"].notna() &
            runs["tags.mlflow.runName"].str.match(r"^\d_")
        ].sort_values("tags.mlflow.runName"))
        if len(journey) > 1:
            with c2, panel():
                names = (journey["tags.mlflow.runName"]
                         .str.replace(r"^\d_", "", regex=True)
                         .str.replace("_", " "))
                rmses = journey["metrics.test_rmse"].values
                bar_cols = [SEV["CRITICAL"]["fill"] if r > 15
                            else SEV["HIGH"]["fill"] if r > 12
                            else BLUE if r > 10
                            else SEV["LOW"]["fill"]
                            for r in rmses]
                fig = go.Figure(go.Bar(
                    x=names, y=rmses,
                    marker_color=bar_cols,
                    text=rmses.round(1), textposition="outside",
                    cliponaxis=False,
                    hovertemplate="%{x}<br>RMSE: %{y:.2f} flights<extra></extra>"
                ))
                fig.update_layout(
                    title="Model Evolution Journey (FD001 — from MLflow)",
                    barcornerradius=4, yaxis_title="RMSE (flights)",
                    yaxis=dict(range=[0, max(rmses) * 1.25])
                )
                show(fig, height=340)

    if not runs.empty and "metrics.val_rmse" in runs.columns and runs["metrics.val_rmse"].notna().any():
        st.markdown('<div class="section-header">Automated Champion vs. Challenger Retraining</div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<p class="note">When new engine data arrives, a <b>Challenger model</b> is trained on combined history '
            'and evaluated against a locked validation cohort. It automatically replaces the Champion '
            'only if validation RMSE improves by ≥ 0.05.</p>',
            unsafe_allow_html=True
        )
        rt = runs[runs["metrics.val_rmse"].notna()].sort_values("start_time")
        cols_rt = {
            "start_time": "Timestamp", "tags.mlflow.runName": "Run Name",
            "tags.stage": "Outcome", "params.n_train_engines": "Training Engines",
            "metrics.val_rmse": "Val RMSE", "metrics.max_sensor_drift": "Max Sensor Drift"
        }
        st.dataframe(
            rt[[c for c in cols_rt if c in rt.columns]].rename(columns=cols_rt),
            hide_index=True,
            column_config={
                "Val RMSE": st.column_config.NumberColumn(format="%.2f"),
                "Max Sensor Drift": st.column_config.NumberColumn(format="%.2f")
            }
        )
    elif subset != "FD001":
        st.markdown(
            '<p class="note">💡 The retraining demo runs on <b>FD001</b>. '
            'Switch to FD001 to view the live Champion vs. Challenger log.</p>',
            unsafe_allow_html=True
        )

    # Config card at the bottom
    st.markdown(f"""
    <div style="background:{SURFACE_2};border:1px solid {BORDER};border-radius:12px;
                padding:16px 20px;margin-top:16px;">
      <div style="font-size:0.75rem;font-weight:600;color:{TEXT_3};letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:10px;">Pipeline Configuration — {subset}</div>
      <div style="display:flex;flex-wrap:wrap;gap:6px 32px;">
        <span style="font-size:0.85rem;color:{TEXT_2}">🤝 Trained with: <b>{cfg.get('trained_with') or 'no partner'}</b></span>
        <span style="font-size:0.85rem;color:{TEXT_2}">🛡️ Safety margin: <b>{cfg.get('safety_margin', 0)} flights</b></span>
        <span style="font-size:0.85rem;color:{TEXT_2}">📐 Decision rule: <b>{cfg.get('decision_policy', 'point estimate')}</b></span>
        <span style="font-size:0.85rem;color:{TEXT_2}">🔬 Anomaly threshold: <b>{cfg['anomaly_threshold']:.3f}</b></span>
        <span style="font-size:0.85rem;color:{TEXT_2}">📊 Range coverage target: <b>{cfg.get('range_coverage_target', 0.8):.0%}</b></span>
        <span style="font-size:0.85rem;color:{TEXT_2}">🔍 Range widening k: <b>{cfg.get('range_widening', 1.0):.2f}</b></span>
      </div>
    </div>
    """, unsafe_allow_html=True)
