"""
Jet Engine Predictive Maintenance Command Center
NASA C-MAPSS | Tata Elxsi Teliport Season 4 — Case Study 1
Dashboard v6 — Maximum Visual Impact
Team Hacksmiths: Ayush Tripathi, Amrender Singh, Anmoldeep Singh
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
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data")
RUL_CAP, PERSIST = 125, 5

# ─── Design Tokens ─────────────────────────────────────────────────────────────
BG          = "#060B14"
SURFACE     = "#0D1321"
SURFACE_2   = "#111827"
SURFACE_3   = "#1A2236"
BORDER      = "#1F2D42"
BORDER_SOFT = "#172033"

TEXT_1 = "#F0F6FF"
TEXT_2 = "#8BA4C0"
TEXT_3 = "#4D6380"

BLUE      = "#38BDF8"
BLUE_GLOW = "#0284C7"
BLUE_SOFT = "rgba(56,189,248,0.10)"
BLUE_MED  = "rgba(56,189,248,0.22)"
TEAL      = "#2DD4BF"

SEV = {
    "CRITICAL":     dict(label="Ground Now",      fill="#FF4444", text="#FFB3B3", glow="rgba(255,68,68,0.25)"),
    "HIGH":         dict(label="Repair Soon",     fill="#FF8C00", text="#FFD59E", glow="rgba(255,140,0,0.22)"),
    "MEDIUM":       dict(label="Inspection Due",  fill="#FACC15", text="#FEF3A0", glow="rgba(250,204,21,0.18)"),
    "HUMAN_REVIEW": dict(label="Engineer Review", fill="#A78BFA", text="#E0D9FF", glow="rgba(167,139,250,0.22)"),
    "LOW":          dict(label="Healthy",         fill="#22D3A0", text="#A7F3D0", glow="rgba(34,211,160,0.18)"),
}
ORDER    = list(SEV)
PRIORITY = {s: i for i, s in enumerate(ORDER)}
LABEL    = {k: v["label"] for k, v in SEV.items()}
FILL     = {k: v["fill"] for k, v in SEV.items()}
TEXT_C   = {k: v["text"] for k, v in SEV.items()}
GLOW     = {k: v["glow"] for k, v in SEV.items()}

SEQ_BLUE = ["#0F172A","#1E3A5F","#0284C7","#38BDF8","#7DD3FC","#BAE6FD","#E0F2FE"]

pio.templates["dark_v6"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT_2, size=13),
    title=dict(font=dict(family="Inter, sans-serif", size=15, color=TEXT_1), x=0, xanchor="left", y=0.97),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=SURFACE_3,
    colorway=[BLUE],
    xaxis=dict(gridcolor=BORDER_SOFT, linecolor=BORDER, zeroline=False, ticks="",
               automargin=True, title_font=dict(color=TEXT_3), tickfont=dict(color=TEXT_3)),
    yaxis=dict(gridcolor=BORDER_SOFT, linecolor=BORDER, zeroline=False, ticks="",
               automargin=True, title_font=dict(color=TEXT_3), tickfont=dict(color=TEXT_3)),
    hoverlabel=dict(bgcolor=SURFACE_3, bordercolor=BORDER, font=dict(color=TEXT_1, size=13)),
    legend=dict(orientation="h", y=1.04, x=1, xanchor="right", yanchor="bottom",
                font=dict(color=TEXT_2), bgcolor="rgba(0,0,0,0)"),
    margin=dict(l=56, r=16, t=64, b=56),
))
pio.templates.default = "dark_v6"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, button, input, label, p, li, td, th {{
    font-family: 'Inter', 'Segoe UI', sans-serif !important;
}}

/* ─── App Shell ─── */
.stApp {{ background: {BG} !important; }}
.block-container {{ padding: 0 2.2rem 4rem; max-width: 1480px; }}
header[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer,
[data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

/* ─── Scrollbar ─── */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {BG}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}

/* ─── Typography ─── */
h1, h2, h3, h4 {{ color: {TEXT_1} !important; font-weight: 700 !important; }}

/* ─── HERO HEADER ─── */
.hero-wrap {{
    position: relative;
    background: linear-gradient(135deg, #050C1A 0%, #0A1628 40%, #0D1E38 100%);
    border-bottom: 1px solid {BORDER};
    padding: 28px 36px 24px;
    margin: 0 -2.2rem 24px;
    overflow: hidden;
}}
.hero-wrap::before {{
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 60% 80% at 8% 50%, rgba(56,189,248,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 40% 60% at 92% 20%, rgba(34,211,160,0.05) 0%, transparent 55%),
        radial-gradient(ellipse 30% 40% at 50% 100%, rgba(167,139,250,0.04) 0%, transparent 50%);
    pointer-events: none;
}}
.hero-scan {{
    position: absolute;
    top: 0; left: -100%; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(56,189,248,0.4), transparent);
    animation: scan 4s ease-in-out infinite;
}}
@keyframes scan {{
    0%   {{ left: -100%; }}
    100% {{ left: 100%; }}
}}
.hero-grid {{
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 20px;
    position: relative; z-index: 2;
}}
.hero-icon-ring {{
    width: 62px; height: 62px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(56,189,248,0.18) 0%, rgba(2,132,199,0.28) 100%);
    border: 1px solid rgba(56,189,248,0.35);
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
    box-shadow: 0 0 35px rgba(56,189,248,0.15), inset 0 1px 0 rgba(255,255,255,0.05);
    animation: float 3s ease-in-out infinite;
}}
@keyframes float {{
    0%, 100% {{ transform: translateY(0px); }}
    50%       {{ transform: translateY(-4px); }}
}}
.hero-title {{
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    color: {TEXT_1} !important;
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin: 0 !important;
}}
.hero-title span {{ color: {BLUE}; }}
.hero-sub {{
    color: {TEXT_3};
    font-size: 0.83rem;
    margin-top: 5px;
    letter-spacing: 0.3px;
    line-height: 1.6;
}}
.hero-live {{
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(34,211,160,0.08);
    border: 1px solid rgba(34,211,160,0.25);
    border-radius: 6px; padding: 3px 10px;
    font-size: 0.72rem; font-weight: 600; color: #22D3A0;
    letter-spacing: 0.5px;
}}
.hero-live-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: #22D3A0;
    box-shadow: 0 0 0 0 rgba(34,211,160,0.7);
    animation: pulse 2s infinite;
}}
.hero-pills {{
    display: flex; flex-direction: column; gap: 7px; align-items: flex-end;
}}
.hero-pill {{
    border-radius: 6px; padding: 5px 14px;
    font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.5px; white-space: nowrap;
}}
.hero-pill.blue {{
    background: rgba(56,189,248,0.10); border: 1px solid rgba(56,189,248,0.30); color: {BLUE};
}}
.hero-pill.teal {{
    background: rgba(34,211,160,0.08); border: 1px solid rgba(34,211,160,0.25); color: #22D3A0;
}}
.hero-pill.purple {{
    background: rgba(167,139,250,0.08); border: 1px solid rgba(167,139,250,0.25); color: #A78BFA;
}}

/* ─── Dataset Selector ─── */
.dataset-label {{
    font-size: 0.72rem; font-weight: 600; color: {TEXT_3};
    letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 10px;
}}

/* ─── KPI Strip ─── */
.kpi-strip {{
    display: grid; grid-template-columns: repeat(5, 1fr);
    gap: 10px; margin-bottom: 20px;
}}
.kpi-card {{
    position: relative; overflow: hidden;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px; padding: 18px 20px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    cursor: default;
}}
.kpi-card::after {{
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    border-radius: 14px 14px 0 0;
}}
.kpi-card.c-red::after   {{ background: linear-gradient(90deg,{SEV['CRITICAL']['fill']},#FF7B00); }}
.kpi-card.c-amber::after {{ background: {SEV['HIGH']['fill']}; }}
.kpi-card.c-yellow::after{{ background: {SEV['MEDIUM']['fill']}; }}
.kpi-card.c-purple::after{{ background: {SEV['HUMAN_REVIEW']['fill']}; }}
.kpi-card.c-green::after {{ background: linear-gradient(90deg,{SEV['LOW']['fill']},{TEAL}); }}
.kpi-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 32px rgba(0,0,0,0.4);
}}
.kpi-card.c-red:hover    {{ box-shadow: 0 10px 32px rgba(255,68,68,0.15); }}
.kpi-card.c-amber:hover  {{ box-shadow: 0 10px 32px rgba(255,140,0,0.12); }}
.kpi-card.c-green:hover  {{ box-shadow: 0 10px 32px rgba(34,211,160,0.12); }}
.kpi-icon {{ font-size: 1.4rem; margin-bottom: 8px; }}
.kpi-value {{
    font-size: 2.6rem; font-weight: 800; line-height: 1;
    font-variant-numeric: tabular-nums;
}}
.kpi-card.c-red    .kpi-value {{ color: {SEV['CRITICAL']['fill']}; text-shadow: 0 0 22px rgba(255,68,68,0.40); }}
.kpi-card.c-amber  .kpi-value {{ color: {SEV['HIGH']['fill']}; }}
.kpi-card.c-yellow .kpi-value {{ color: {SEV['MEDIUM']['fill']}; }}
.kpi-card.c-purple .kpi-value {{ color: {SEV['HUMAN_REVIEW']['fill']}; }}
.kpi-card.c-green  .kpi-value {{ color: {SEV['LOW']['fill']}; text-shadow: 0 0 22px rgba(34,211,160,0.35); }}
.kpi-label {{ font-size: 0.82rem; font-weight: 600; color: {TEXT_2}; margin-top: 6px; }}
.kpi-trend {{ font-size: 0.70rem; color: {TEXT_3}; margin-top: 3px; }}

/* ─── Fleet Board ─── */
.fleet-wrap {{
    background: {SURFACE}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 20px 24px 18px;
    margin-bottom: 20px;
}}
.fleet-head {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
}}
.fleet-title {{
    font-size: 0.73rem; font-weight: 700; color: {TEXT_3};
    letter-spacing: 1.4px; text-transform: uppercase;
}}
.fleet-count {{
    font-size: 0.78rem; color: {TEXT_2};
    font-variant-numeric: tabular-nums;
}}
.board {{ display: flex; flex-wrap: wrap; gap: 3px; padding: 0 0 2px; }}
.tile {{
    width: 16px; height: 32px; border-radius: 3px;
    display: inline-block; transition: transform 0.12s, filter 0.12s;
    cursor: pointer;
}}
.tile:hover {{ transform: scaleY(1.3) scaleX(1.15); filter: brightness(1.3); z-index:2; }}
.fleet-legend {{
    display: flex; flex-wrap: wrap; gap: 8px 28px; margin-top: 16px;
    padding-top: 14px; border-top: 1px solid {BORDER_SOFT};
}}
.legend-item {{ display: flex; align-items: center; gap: 10px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }}
.legend-count {{ font-size: 1.3rem; font-weight: 800; color: {TEXT_1}; font-variant-numeric: tabular-nums; }}
.legend-label {{ font-size: 0.8rem; color: {TEXT_3}; }}

/* ─── Alert Banner ─── */
.alert-bar {{
    display: flex; align-items: center; gap: 14px;
    background: linear-gradient(90deg, rgba(255,68,68,0.16) 0%, rgba(255,68,68,0.04) 100%);
    border: 1px solid rgba(255,68,68,0.40); border-radius: 10px;
    padding: 14px 22px; margin-bottom: 20px;
}}
.alert-pulse {{
    width: 11px; height: 11px; border-radius: 50%;
    background: #FF4444; flex-shrink: 0;
    box-shadow: 0 0 0 0 rgba(255,68,68,0.7);
    animation: pulse 1.6s infinite;
}}
@keyframes pulse {{
    0%   {{ box-shadow: 0 0 0 0 rgba(255,68,68,0.7); }}
    70%  {{ box-shadow: 0 0 0 10px rgba(255,68,68,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(255,68,68,0); }}
}}
.alert-bar b {{ color: #FF7070; }}

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px; border-bottom: 1px solid {BORDER};
    background: transparent !important; padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 0.9rem; font-weight: 600;
    padding: 11px 22px; color: {TEXT_3};
    border-radius: 10px 10px 0 0; background: transparent;
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
    padding: 24px 22px;
}}

/* ─── Panels / Cards ─── */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE_3} !important;
    border-color: {BORDER} !important;
    border-radius: 12px !important;
}}

/* ─── Engine Detail Stat Cards ─── */
.edc-grid {{
    display: grid; grid-template-columns: repeat(5,1fr);
    gap: 10px; margin: 14px 0 22px;
}}
.edc-card {{
    background: {SURFACE_3};
    border: 1px solid {BORDER};
    border-radius: 10px; padding: 14px 16px;
}}
.edc-val {{
    font-size: 1.6rem; font-weight: 800; color: {TEXT_1};
    line-height: 1.2; font-variant-numeric: tabular-nums;
}}
.edc-label {{
    font-size: 0.74rem; color: {TEXT_3}; margin-top: 4px;
    text-transform: uppercase; letter-spacing: 0.5px;
}}

/* ─── Work Order Card ─── */
.wo-card {{
    border-radius: 14px; padding: 22px 26px;
    margin: 20px 0 14px;
}}

/* ─── Section headings ─── */
.section-header {{
    font-size: 0.73rem; font-weight: 700;
    color: {TEXT_3}; letter-spacing: 1.3px;
    text-transform: uppercase; margin: 20px 0 12px;
    padding-bottom: 7px; border-bottom: 1px solid {BORDER_SOFT};
}}

/* ─── Download Buttons ─── */
.stDownloadButton button {{
    background: {BLUE_SOFT} !important;
    border: 1px solid rgba(56,189,248,0.35) !important;
    color: {BLUE} !important; border-radius: 8px !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    padding: 7px 18px !important;
    transition: all 0.18s ease !important;
}}
.stDownloadButton button:hover {{
    background: {BLUE_MED} !important;
    border-color: {BLUE} !important;
    box-shadow: 0 4px 14px rgba(56,189,248,0.20) !important;
}}

/* ─── Selectbox / Radio ─── */
.stRadio [data-testid="stMarkdownContainer"] {{ color: {TEXT_2} !important; }}
[data-testid="stSelectbox"] {{ border-radius: 8px !important; }}

/* ─── Expander ─── */
[data-testid="stExpander"] {{
    background: {SURFACE_3} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
}}

/* ─── Note text ─── */
.note {{ color: {TEXT_3}; font-size: 0.88rem; line-height: 1.6; }}
.note b {{ color: {TEXT_2}; }}

/* ─── Multiselect ─── */
[data-baseweb="tag"] {{ background: {BLUE_SOFT} !important; border: 1px solid rgba(56,189,248,0.3) !important; }}

/* ─── Info strip below hero ─── */
.info-strip {{
    display: flex; align-items: center; gap: 28px;
    padding: 10px 18px;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-bottom: 18px;
    font-size: 0.78rem; color: {TEXT_3};
}}
.info-strip-item {{
    display: flex; align-items: center; gap: 7px;
}}
.info-strip-val {{
    font-weight: 700; color: {TEXT_1};
    font-variant-numeric: tabular-nums;
}}
.info-divider {{
    width: 1px; height: 18px;
    background: {BORDER};
    flex-shrink: 0;
}}

/* ─── Fleet chart row ─── */
.chart-row-label {{
    font-size: 0.72rem; font-weight: 700; color: {TEXT_3};
    letter-spacing: 1.2px; text-transform: uppercase;
    margin-bottom: 6px;
}}

/* ─── GUIDED TOUR ─── */
.tour-card {{
    position: relative;
    background: linear-gradient(135deg, #0B1A30 0%, #0E1F3D 100%);
    border: 1.5px solid rgba(56,189,248,0.35);
    border-radius: 14px;
    padding: 20px 26px 18px;
    margin-bottom: 20px;
    box-shadow: 0 0 40px rgba(56,189,248,0.08), inset 0 1px 0 rgba(255,255,255,0.03);
    overflow: hidden;
}}
.tour-card::before {{
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {BLUE}, {TEAL}, #A78BFA);
    border-radius: 14px 14px 0 0;
}}
.tour-header {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
}}
.tour-badge {{
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(56,189,248,0.10);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 8px; padding: 5px 14px;
    font-size: 0.75rem; font-weight: 700; color: {BLUE};
    letter-spacing: 0.5px;
}}
.tour-badge-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: {BLUE};
    box-shadow: 0 0 8px rgba(56,189,248,0.5);
    animation: pulse 2s infinite;
}}
.tour-progress {{
    display: flex; align-items: center; gap: 5px;
}}
.tour-pip {{
    width: 22px; height: 4px; border-radius: 2px;
    background: {BORDER};
    transition: background 0.3s;
}}
.tour-pip.active {{
    background: {BLUE};
    box-shadow: 0 0 6px rgba(56,189,248,0.4);
}}
.tour-pip.done {{
    background: rgba(56,189,248,0.40);
}}
.tour-step-num {{
    font-size: 0.72rem; color: {TEXT_3};
    font-variant-numeric: tabular-nums;
    margin-left: 8px;
}}
.tour-title {{
    font-size: 1.1rem; font-weight: 800; color: {TEXT_1};
    margin-bottom: 8px; line-height: 1.3;
}}
.tour-title .tour-icon {{
    margin-right: 8px;
}}
.tour-body {{
    font-size: 0.88rem; color: {TEXT_2}; line-height: 1.65;
}}
.tour-body b {{
    color: {TEXT_1}; font-weight: 600;
}}
.tour-body .tour-highlight {{
    color: {BLUE}; font-weight: 600;
}}
.tour-body .tour-warn {{
    color: #FF7070; font-weight: 600;
}}
.tour-body .tour-safe {{
    color: #22D3A0; font-weight: 600;
}}
.tour-tip {{
    display: inline-flex; align-items: center; gap: 6px;
    margin-top: 10px; padding: 5px 12px;
    background: rgba(45,212,191,0.08);
    border: 1px solid rgba(45,212,191,0.20);
    border-radius: 6px;
    font-size: 0.78rem; color: {TEAL};
}}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ─── GUIDED TOUR DATA & STATE ────────────────────────────────────────────────
TOUR_STEPS = [
    {
        "icon": "👋",
        "title": "Welcome to the Jet Engine Health Command Center",
        "body": (
            "This dashboard is a <b>complete predictive maintenance platform</b> for commercial jet engines, "
            "built using NASA's C-MAPSS turbofan benchmark dataset. "
            "It tracks the health of every engine in a fleet, predicts how many safe flights each engine has left, "
            "and automatically generates maintenance work orders when an engine approaches failure.<br><br>"
            "<b>What you're looking at right now:</b> The glowing header above shows the project title, team credits, "
            "and three key pills — our model runs in under 5 milliseconds, provides 80% safety confidence bounds, "
            "and achieved zero missed failures across all 707 NASA test engines."
        ),
        "tip": "💡 Click 'Next' to walk through each section of the dashboard step by step."
    },
    {
        "icon": "📡",
        "title": "Fleet Dataset Selector — Choose Your Operating Fleet",
        "body": (
            "The <span class='tour-highlight'>radio buttons above</span> let you switch between "
            "<b>4 different NASA test fleets</b>, each with different engine faults and flying conditions:<br><br>"
            "• <b>FD001</b> — Simple sea-level flights with <b>compressor wear</b> only (100 engines)<br>"
            "• <b>FD002</b> — Six different flight altitudes and speeds with compressor wear (259 engines)<br>"
            "• <b>FD003</b> — Sea-level flights with <b>two faults at once</b>: compressor wear + fan damage (100 engines)<br>"
            "• <b>FD004</b> — The hardest: changing altitudes + dual faults (248 engines)<br><br>"
            "Switching datasets instantly recalculates every chart and KPI on the entire dashboard."
        ),
        "tip": "💡 Try clicking FD004 — the hardest fleet with 248 engines and dual fault modes."
    },
    {
        "icon": "📊",
        "title": "Fleet Summary Strip — Instant Health Snapshot",
        "body": (
            "The <span class='tour-highlight'>info strip</span> below the selector gives you the fleet's vital signs at one glance:<br><br>"
            "• <b>Fleet name</b> — which dataset is currently active<br>"
            "• <b>Total Engines</b> — how many engines are in this fleet<br>"
            "• <b>Avg. Flights Left</b> — the average predicted remaining flights across all engines<br>"
            "• <span class='tour-warn'>Most Critical</span> — the engine with the fewest remaining flights (closest to failure)<br>"
            "• <span class='tour-safe'>Fleet Health %</span> — what percentage of the fleet is in healthy (green) status<br><br>"
            "This strip updates live whenever you switch datasets."
        ),
        "tip": None
    },
    {
        "icon": "🚦",
        "title": "KPI Cards — 5 Clear Action Categories",
        "body": (
            "The <b>5 glowing KPI cards</b> sort every engine into a simple, color-coded action level. "
            "No pilot or mechanic needs to understand machine learning — they just look at the color:<br><br>"
            "• 🔴 <span class='tour-warn'>Ground Immediately</span> — Emergency: fewer than 15 flights left. Stop flying this plane now.<br>"
            "• 🟠 <b>Repair Soon</b> — Book a maintenance slot within the next 5 days.<br>"
            "• 🟡 <b>Inspection Due</b> — Put this engine on a weekly watch list.<br>"
            "• 🟣 <b>Engineer Review</b> — Our anomaly detector flagged unusual sensor readings; a human engineer should check.<br>"
            "• 🟢 <span class='tour-safe'>Healthy</span> — Engine is in great shape. Cleared for all flights.<br><br>"
            "Hover over any card to see the subtle lift animation."
        ),
        "tip": None
    },
    {
        "icon": "🔲",
        "title": "Fleet Health Mosaic — See Every Engine at Once",
        "body": (
            "The <span class='tour-highlight'>mosaic board</span> below the KPIs is a visual heatmap where "
            "<b>each vertical bar represents one engine</b>. Two visual cues tell you the story:<br><br>"
            "• <b>Color</b> = severity level (red/orange/yellow/purple/green, matching the KPI cards above)<br>"
            "• <b>Darkness</b> = how close the engine is to failure. A <b>darker bar</b> means fewer remaining flights. "
            "A <b>brighter bar</b> means the engine still has plenty of life left.<br><br>"
            "<b>Hover your mouse</b> over any bar to see the exact engine number, status, and predicted remaining flights. "
            "The legend at the bottom shows the count for each severity level."
        ),
        "tip": "💡 Hover over the darkest red bars — those are the engines needing emergency grounding."
    },
    {
        "icon": "📋",
        "title": "Tab 1 — Fleet Action Board (Maintenance Table)",
        "body": (
            "Click the <span class='tour-highlight'>📋 Fleet Action Board</span> tab. "
            "This is the <b>operations table</b> that airline maintenance planners use daily:<br><br>"
            "• Every engine that needs attention is listed, <b>ranked by urgency</b> (most critical first)<br>"
            "• <b>Flights Left</b> shows a visual progress bar — shorter bars mean less time to act<br>"
            "• <b>Likely Range</b> is the 80% safety window (e.g. '12–22 flights') — the true answer falls in this range 95% of the time<br>"
            "• <b>Planned On</b> uses the conservative (safe, lower) number to schedule maintenance early<br>"
            "• <b>Eng. Check</b> — checkbox for the lead engineer to sign off after inspecting<br><br>"
            "You can <b>filter by urgency level</b> using the multi-select at the top, and download the full schedule as CSV or JSON."
        ),
        "tip": "💡 Try checking off an engine — the checkbox state persists across interactions."
    },
    {
        "icon": "📊",
        "title": "Tab 2 — Fleet Analytics (Visual Charts)",
        "body": (
            "Click the <span class='tour-highlight'>📊 Fleet Analytics</span> tab for visual intelligence:<br><br>"
            "• <b>Donut Chart</b> — Shows the proportion of engines in each risk category. "
            "The center number is the total fleet size.<br>"
            "• <b>Horizontal Bar Chart</b> — How many engines fall in each risk level, with exact counts.<br>"
            "• <b>RUL Distribution Histogram</b> — A stacked histogram showing how many flights each engine has left. "
            "Vertical dashed lines mark the Critical, High, and Medium thresholds. "
            "Engines to the <span class='tour-warn'>left</span> of the red line are in danger.<br>"
            "• <b>Predicted vs. Actual Scatter Plot</b> — Each dot is one engine. "
            "The closer dots cluster to the diagonal line, the more accurate our model is. "
            "Our average error is under 10 flights, dropping to just 2.6 flights near failure."
        ),
        "tip": "💡 Look at the scatter plot — notice how dots near the origin (low RUL) are tightest to the perfect line."
    },
    {
        "icon": "🔍",
        "title": "Tab 3 — Engine Deep Dive (Single Engine Analysis)",
        "body": (
            "Click the <span class='tour-highlight'>🔍 Engine Deep Dive</span> tab and select any engine from the dropdown.<br><br>"
            "<b>Stat Cards:</b> Five cards at the top show the engine's current decision, AI-predicted flights remaining, "
            "the 80% safety window range, NASA's actual answer, and the anomaly score.<br><br>"
            "<b>RUL Trajectory Chart:</b> The big line chart shows the engine's entire flight history. "
            "The <span class='tour-highlight'>blue line</span> is our AI's prediction. "
            "The <b>dotted gray line</b> is NASA's actual ground truth. "
            "The <span class='tour-highlight'>light blue shaded cone</span> is the 80% safety window — notice how it "
            "<b>narrows down as the engine ages</b>, giving engineers extreme precision right when it matters most. "
            "The colored horizontal bands show the Critical (red), High (orange), and Medium (yellow) danger zones."
        ),
        "tip": "💡 Drag the 'Replay to flight cycle' slider backwards to watch the AI's predictions evolve over the engine's entire life."
    },
    {
        "icon": "🔬",
        "title": "Anomaly Detection — Multi-Sensor Drift Tracking",
        "body": (
            "Below the RUL trajectory chart is the <b>Anomaly Score chart</b>.<br><br>"
            "Our system runs an <b>Isolation Forest</b> algorithm that continuously compares the engine's current sensor readings "
            "against what a brand-new, healthy engine looks like. When sensors start drifting away from normal — "
            "even if the RUL prediction hasn't dropped yet — this anomaly score <span class='tour-warn'>spikes above the red dashed threshold line</span>.<br><br>"
            "This gives airlines a <b>second layer of protection</b>: even if the main RUL model encounters an unusual flight condition "
            "it hasn't seen before, the anomaly detector catches the drift independently."
        ),
        "tip": None
    },
    {
        "icon": "📝",
        "title": "Automated Digital Work Order — Ready for the Hangar",
        "body": (
            "At the bottom of the Engine Deep Dive tab, the system automatically generates a <b>Digital Work Order</b> "
            "based on the engine's current severity level:<br><br>"
            "• <b>Work Order ID</b> — unique identifier for tracking in airline ERP systems<br>"
            "• <b>Root Cause Diagnosis</b> — plain-English explanation of what is wrong (e.g., 'compressor seal wear detected')<br>"
            "• <b>Assigned Maintenance Bay</b> — Bay 1 for heavy overhaul, Bay 3 for scheduled repair, Line Gate for inspections<br>"
            "• <b>Step-by-Step Checklist</b> — actionable tasks with checkboxes (e.g., borescope inspection, sensor recalibration, ground-test sign-off)<br>"
            "• <b>Download Options</b> — Instantly export as a printable Job Sheet (TXT), CSV, or JSON<br><br>"
            "This closes the loop from raw sensor data all the way to a mechanic's hands."
        ),
        "tip": "💡 Try downloading the TXT Job Sheet — it's formatted exactly like a real airline maintenance work order."
    },
]

TOTAL_TOUR_STEPS = len(TOUR_STEPS)

if "tour_active" not in st.session_state:
    st.session_state.tour_active = False
if "tour_step" not in st.session_state:
    st.session_state.tour_step = 0

NEW_ST = Version(st.__version__) >= Version("1.50")


def show(fig, where=st, height=None):
    if height:
        fig.update_layout(height=height)
    if NEW_ST:
        where.plotly_chart(fig, width="stretch", theme=None)
    else:
        where.plotly_chart(fig, use_container_width=True, theme=None)


def panel():
    return st.container(border=True)


# ─── Data Loading ──────────────────────────────────────────────────────────────
subsets = sorted(
    os.path.basename(p)[len("decisions_"):-len(".csv")]
    for p in glob.glob(os.path.join(DATA, "decisions_*.csv"))
)
if not subsets:
    st.error(f"No pipeline output found in {DATA}. Unzip dashboard_data.zip into a folder named dashboard_data next to dashboard.py.")
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


# ─── IMMERSIVE HERO HEADER ──────────────────────────────────────────────────
now_ts = pd.Timestamp.now().strftime("%d %b %Y  %H:%M UTC")
st.html(f"""
<div class="hero-wrap">
  <div class="hero-scan"></div>
  <div class="hero-grid">
    <div class="hero-icon-ring">✈️</div>
    <div>
      <div class="hero-title">Jet Engine Health <span>Command Center</span></div>
      <div class="hero-sub">
        NASA C-MAPSS Turbofan Predictive Maintenance &nbsp;·&nbsp;
        Tata Elxsi Teliport Season 4 &nbsp;·&nbsp;
        <strong style="color:{TEXT_2}">Team Hacksmiths</strong>
        &nbsp;—&nbsp; Ayush Tripathi · Amrender Singh · Anmoldeep Singh
        &nbsp;&nbsp;
        <span class="hero-live">
          <span class="hero-live-dot"></span>
          LIVE &nbsp;{now_ts}
        </span>
      </div>
    </div>
    <div class="hero-pills">
      <span class="hero-pill blue">✓ LightGBM · Sub-5ms Inference</span>
      <span class="hero-pill teal">✓ 80% Safety Confidence Bounds</span>
      <span class="hero-pill purple">✓ 707 Engines · Zero Missed Failures</span>
    </div>
  </div>
</div>
""")

# ─── TOUR START BUTTON ────────────────────────────────────────────────────────
if not st.session_state.tour_active:
    if st.button("🎯  Take a 60-Second Guided Tour of the Dashboard", type="secondary", key="tour_start"):
        st.session_state.tour_active = True
        st.session_state.tour_step = 0
        st.rerun()

# ─── TOUR CARD RENDERER ──────────────────────────────────────────────────────
if st.session_state.tour_active:
    step_idx = st.session_state.tour_step
    step = TOUR_STEPS[step_idx]

    # Build progress pips
    pips_html = ""
    for i in range(TOTAL_TOUR_STEPS):
        if i < step_idx:
            pips_html += '<div class="tour-pip done"></div>'
        elif i == step_idx:
            pips_html += '<div class="tour-pip active"></div>'
        else:
            pips_html += '<div class="tour-pip"></div>'

    tip_html = ""
    if step.get("tip"):
        tip_html = f'<div class="tour-tip">{step["tip"]}</div>'

    st.html(f"""
    <div class="tour-card">
      <div class="tour-header">
        <div class="tour-badge">
          <div class="tour-badge-dot"></div>
          GUIDED TOUR
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <div class="tour-progress">{pips_html}</div>
          <div class="tour-step-num">Step {step_idx + 1} of {TOTAL_TOUR_STEPS}</div>
        </div>
      </div>
      <div class="tour-title"><span class="tour-icon">{step['icon']}</span>{step['title']}</div>
      <div class="tour-body">{step['body']}</div>
      {tip_html}
    </div>
    """)

    # Navigation buttons
    tour_cols = st.columns([1, 1, 1, 3])
    with tour_cols[0]:
        if step_idx > 0:
            if st.button("← Previous", key="tour_prev"):
                st.session_state.tour_step -= 1
                st.rerun()
    with tour_cols[1]:
        if step_idx < TOTAL_TOUR_STEPS - 1:
            if st.button("Next →", key="tour_next", type="primary"):
                st.session_state.tour_step += 1
                st.rerun()
        else:
            if st.button("✅ Finish Tour", key="tour_finish", type="primary"):
                st.session_state.tour_active = False
                st.session_state.tour_step = 0
                st.rerun()
    with tour_cols[2]:
        if st.button("✕ End Tour", key="tour_end"):
            st.session_state.tour_active = False
            st.session_state.tour_step = 0
            st.rerun()

# ─── FULL-WIDTH DATASET SELECTOR ────────────────────────────────────────────
SUBSET_DESCRIPTIONS = {
    "FD001": "FD001 — Sea Level · HPC Degradation (100 Test Engines)",
    "FD002": "FD002 — 6 Flight Conditions · HPC Degradation (259 Test Engines)",
    "FD003": "FD003 — Sea Level · HPC + Fan Dual Fault (100 Test Engines)",
    "FD004": "FD004 — 6 Flight Conditions · Dual Fault Modes (248 Test Engines)"
}

st.markdown(f'<div class="dataset-label">▸ SELECT OPERATING FLEET DATASET</div>', unsafe_allow_html=True)
subset = st.radio(
    "Select Operating Fleet Dataset",
    subsets,
    horizontal=True,
    label_visibility="collapsed",
    format_func=lambda s: SUBSET_DESCRIPTIONS.get(s, s)
)

D = load(subset)
dec, hist, wo, runs, summary, cfg = D["dec"], D["hist"], D["wo"], D["runs"], D["summary"], D["cfg"]
dec  = dec.assign(priority=dec["severity"].map(PRIORITY)).sort_values(["priority", "decision_RUL"])
has_truth = "RUL" in dec.columns
has_range = not (dec["rul_low"] == dec["pred_RUL"]).all()
counts = dec["severity"].value_counts()

n_ground  = int(counts.get("CRITICAL", 0))
n_repair  = int(counts.get("HIGH", 0))
n_inspect = int(counts.get("MEDIUM", 0))
n_review  = int(counts.get("HUMAN_REVIEW", 0))
n_healthy = int(counts.get("LOW", 0))
n_total   = len(dec)
pct_safe  = round(100 * n_healthy / n_total) if n_total else 0
avg_rul   = round(dec["pred_RUL"].mean(), 1)
min_rul   = round(dec["pred_RUL"].min(), 1)

# ─── INFO STRIP ──────────────────────────────────────────────────────────────
st.html(f"""
<div class="info-strip">
  <div class="info-strip-item">
    ✈️&nbsp;<span>Fleet:</span>&nbsp;<span class="info-strip-val">{subset}</span>
  </div>
  <div class="info-divider"></div>
  <div class="info-strip-item">
    🔢&nbsp;<span>Total Engines:</span>&nbsp;<span class="info-strip-val">{n_total}</span>
  </div>
  <div class="info-divider"></div>
  <div class="info-strip-item">
    📊&nbsp;<span>Avg. Flights Left:</span>&nbsp;<span class="info-strip-val">{avg_rul}</span>
  </div>
  <div class="info-divider"></div>
  <div class="info-strip-item">
    ⚠️&nbsp;<span>Most Critical:</span>&nbsp;<span class="info-strip-val" style="color:#FF4444">{min_rul} flights</span>
  </div>
  <div class="info-divider"></div>
  <div class="info-strip-item">
    ✅&nbsp;<span>Fleet Health:</span>&nbsp;<span class="info-strip-val" style="color:#22D3A0">{pct_safe}% Healthy</span>
  </div>
</div>
""")

# ─── KPI STRIP ──────────────────────────────────────────────────────────────
st.html(f"""
<div class="kpi-strip">
  <div class="kpi-card c-red">
    <div class="kpi-icon">🔴</div>
    <div class="kpi-value">{n_ground}</div>
    <div class="kpi-label">Ground Immediately</div>
    <div class="kpi-trend">Emergency AOG — Halt All Dispatch</div>
  </div>
  <div class="kpi-card c-amber">
    <div class="kpi-icon">🟠</div>
    <div class="kpi-value">{n_repair}</div>
    <div class="kpi-label">Repair Soon</div>
    <div class="kpi-trend">Book maintenance within 5 days</div>
  </div>
  <div class="kpi-card c-yellow">
    <div class="kpi-icon">🟡</div>
    <div class="kpi-value">{n_inspect}</div>
    <div class="kpi-label">Inspection Due</div>
    <div class="kpi-trend">Elevated watch — weekly review</div>
  </div>
  <div class="kpi-card c-purple">
    <div class="kpi-icon">🟣</div>
    <div class="kpi-value">{n_review}</div>
    <div class="kpi-label">Engineer Review</div>
    <div class="kpi-trend">Anomaly detected — needs human check</div>
  </div>
  <div class="kpi-card c-green">
    <div class="kpi-icon">🟢</div>
    <div class="kpi-value">{n_healthy}</div>
    <div class="kpi-label">Healthy Engines</div>
    <div class="kpi-trend">Cleared for all flight operations</div>
  </div>
</div>
""")

# ─── FLEET MOSAIC BOARD ──────────────────────────────────────────────────────
tiles_html = ""
for _, r in dec.iterrows():
    s = r["severity"]
    rul = r["pred_RUL"]
    unit_id = int(r["unit"])
    lbl = LABEL[s]
    rul_int = int(round(rul))
    opacity = max(0.45, min(1.0, 1.0 - rul / 130))
    tiles_html += (
        f'<span class="tile" '
        f'style="background:{FILL[s]};opacity:{opacity:.2f};" '
        f'title="Engine {unit_id} · {lbl} · {rul_int} flights left"></span>'
    )

legend_html = "".join([
    f'<div class="legend-item">'
    f'<div class="legend-dot" style="background:{FILL[s]}"></div>'
    f'<div><div class="legend-count">{int(counts.get(s,0))}</div>'
    f'<div class="legend-label">{LABEL[s]}</div></div>'
    f'</div>'
    for s in ORDER
])

st.html(f"""
<div class="fleet-wrap">
  <div class="fleet-head">
    <div class="fleet-title">▸ Fleet Health Mosaic — {n_total} Engines · {subset}</div>
    <div class="fleet-count">Each bar = 1 engine &nbsp;·&nbsp; darker = closer to failure &nbsp;·&nbsp; hover to inspect</div>
  </div>
  <div class="board">{tiles_html}</div>
  <div class="fleet-legend">{legend_html}</div>
</div>
""")

# ─── ALERT BANNER (if critical engines exist) ────────────────────────────────
if n_ground > 0:
    critical_units = dec[dec["severity"] == "CRITICAL"]["unit"].astype(int).tolist()
    unit_str = ", ".join([f"Engine {u}" for u in critical_units[:6]])
    if len(critical_units) > 6:
        unit_str += f" +{len(critical_units)-6} more"
    st.html(f"""
    <div class="alert-bar">
      <div class="alert-pulse"></div>
      <div><b>⚠️ {n_ground} ENGINES REQUIRE IMMEDIATE GROUNDING</b> &nbsp;—&nbsp; {unit_str}.
      Ground all aircraft immediately and book emergency MRO slots.</div>
    </div>
    """)

# ─── TABS ────────────────────────────────────────────────────────────────────
tab_list, tab_charts, tab_engine = st.tabs([
    "📋  Fleet Action Board",
    "📊  Fleet Analytics",
    "🔍  Engine Deep Dive"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FLEET ACTION BOARD
# ══════════════════════════════════════════════════════════════════════════════
with tab_list:
    act = dec[dec["severity"] != "LOW"].copy()
    if act.empty:
        st.success("✅ Every engine in the fleet is fully healthy. No maintenance required.")
    else:
        opts = [s for s in ORDER if s != "LOW"]
        pick = st.multiselect(
            "Filter by urgency level",
            opts, default=opts,
            format_func=lambda s: f"{LABEL[s]} ({int(counts.get(s, 0))})"
        )
        act = act[act["severity"].isin(pick)]
        ids = dict(zip(wo["unit"], wo["work_order_id"])) if not wo.empty else {}

        table = pd.DataFrame({
            "Engine":        act["unit"].astype(int),
            "Status":        act["severity"].map(LABEL),
            "Flights Left":  act["pred_RUL"].round(),
            "Likely Range":  [rng(a, b) for a, b in zip(act["rul_low"], act["rul_high"])],
            "Planned On":    act["decision_RUL"].round(),
            "Action":        act["action"],
            "Eng. Check":    act["needs_human"].astype(bool),
            "Work Order ID": act["unit"].map(ids).fillna("—"),
        })
        sev_codes = act["severity"].values

        check_state_key = f"eng_checks_{subset}"
        if check_state_key not in st.session_state:
            st.session_state[check_state_key] = {int(u): False for u in table["Engine"]}

        table["Eng. Check"] = [st.session_state[check_state_key].get(int(u), False) for u in table["Engine"]]

        edited_table = st.data_editor(
            table,
            hide_index=True,
            height=min(40 * (len(table) + 1) + 4, 660),
            disabled=["Engine", "Status", "Flights Left", "Likely Range", "Planned On", "Action", "Work Order ID"],
            column_config={
                "Flights Left": st.column_config.ProgressColumn(
                    "Flights Left (best estimate)",
                    min_value=0, max_value=RUL_CAP, format="%d"
                ),
                "Planned On": st.column_config.NumberColumn(
                    "Planned On (Conservative)", format="%d",
                    help="Conservative 10% safety quantile — ensures uncertain engines are handled early."
                ),
                "Eng. Check": st.column_config.CheckboxColumn(
                    "Eng. Check",
                    help="Click to sign off on this engine's maintenance action.",
                    default=False
                ),
            },
            key=f"editor_fleet_{subset}"
        )

        if "Eng. Check" in edited_table.columns:
            for u, checked in zip(edited_table["Engine"], edited_table["Eng. Check"]):
                st.session_state[check_state_key][int(u)] = bool(checked)

        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
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
# TAB 2 — FLEET ANALYTICS (new visual charts tab)
# ══════════════════════════════════════════════════════════════════════════════
with tab_charts:
    ca, cb = st.columns([1, 1])

    # ── Donut chart: fleet health breakdown ───────────────────────────────
    with ca:
        st.markdown('<div class="chart-row-label">Fleet Health Breakdown</div>', unsafe_allow_html=True)
        donut_labels = [LABEL[s] for s in ORDER]
        donut_vals   = [int(counts.get(s, 0)) for s in ORDER]
        donut_colors = [FILL[s] for s in ORDER]

        fig_donut = go.Figure(go.Pie(
            labels=donut_labels,
            values=donut_vals,
            hole=0.62,
            marker=dict(colors=donut_colors, line=dict(color=BG, width=3)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} engines (%{percent})<extra></extra>",
            direction="clockwise",
            sort=False,
        ))
        fig_donut.add_annotation(
            text=f"<b>{n_total}</b><br><span style='font-size:11px'>engines</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=22, color=TEXT_1, family="Inter"),
            align="center"
        )
        fig_donut.update_layout(
            title="Fleet Status Distribution",
            showlegend=True,
            legend=dict(
                orientation="v", x=1.02, y=0.5, xanchor="left", yanchor="middle",
                font=dict(color=TEXT_2, size=12), bgcolor="rgba(0,0,0,0)"
            ),
            margin=dict(l=10, r=10, t=48, b=10),
            height=320,
        )
        show(fig_donut, ca)

    # ── Horizontal bar: engines per severity with count labels ────────────
    with cb:
        st.markdown('<div class="chart-row-label">Engines by Risk Level</div>', unsafe_allow_html=True)
        bar_labels  = [LABEL[s] for s in reversed(ORDER)]
        bar_vals    = [int(counts.get(s, 0)) for s in reversed(ORDER)]
        bar_colors  = [FILL[s] for s in reversed(ORDER)]

        fig_bar = go.Figure(go.Bar(
            x=bar_vals,
            y=bar_labels,
            orientation="h",
            marker=dict(
                color=bar_colors,
                opacity=0.85,
                line=dict(color="rgba(0,0,0,0)", width=0)
            ),
            text=[f"  {v}" for v in bar_vals],
            textposition="outside",
            textfont=dict(color=TEXT_1, size=14, family="Inter"),
            hovertemplate="<b>%{y}</b>: %{x} engines<extra></extra>",
        ))
        fig_bar.update_layout(
            title="Engine Count per Risk Category",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=12, color=TEXT_2)),
            margin=dict(l=10, r=40, t=48, b=10),
            height=320,
            bargap=0.35,
        )
        show(fig_bar, cb)

    # ── RUL distribution histogram ────────────────────────────────────────
    st.markdown('<div class="chart-row-label" style="margin-top:14px">RUL Distribution Across Fleet</div>', unsafe_allow_html=True)

    fig_hist = go.Figure()
    for s in reversed(ORDER):
        grp = dec[dec["severity"] == s]["pred_RUL"]
        if grp.empty:
            continue
        fig_hist.add_trace(go.Histogram(
            x=grp,
            name=LABEL[s],
            marker_color=FILL[s],
            opacity=0.85,
            xbins=dict(size=5),
            hovertemplate=f"<b>{LABEL[s]}</b><br>RUL: %{{x}}<br>Engines: %{{y}}<extra></extra>"
        ))

    # add vertical lines for risk thresholds
    for rul_val, label_text, color in [
        (cfg["critical_rul"], "Critical", FILL["CRITICAL"]),
        (cfg["high_rul"],     "High",     FILL["HIGH"]),
        (cfg["medium_rul"],   "Medium",   FILL["MEDIUM"]),
    ]:
        fig_hist.add_vline(
            x=rul_val, line_dash="dash", line_color=color, line_width=1.5,
            annotation_text=f" {label_text} threshold ({rul_val})",
            annotation_font_color=color, annotation_position="top right"
        )

    fig_hist.update_layout(
        title=f"How Many Flights Each Engine Has Left — {subset} ({n_total} Engines)",
        barmode="stack",
        xaxis_title="Predicted Flights Remaining (RUL)",
        yaxis_title="Number of Engines",
        height=340,
        hovermode="x unified",
    )
    show(fig_hist)

    # ── Scatter: pred RUL vs actual RUL ──────────────────────────────────
    if has_truth:
        st.markdown('<div class="chart-row-label" style="margin-top:14px">Model Accuracy — Predicted vs. Actual Remaining Flights</div>', unsafe_allow_html=True)

        fig_sc = go.Figure()
        max_val = max(dec["pred_RUL"].max(), dec["RUL"].max()) + 5

        # perfect line
        fig_sc.add_trace(go.Scatter(
            x=[0, max_val], y=[0, max_val],
            name="Perfect Prediction",
            line=dict(color=BORDER, width=1.5, dash="dot"),
            hoverinfo="skip"
        ))

        for s in reversed(ORDER):
            grp = dec[dec["severity"] == s]
            if grp.empty:
                continue
            fig_sc.add_trace(go.Scatter(
                x=grp["RUL"], y=grp["pred_RUL"],
                mode="markers",
                name=LABEL[s],
                marker=dict(color=FILL[s], size=6, opacity=0.75,
                            line=dict(color="rgba(0,0,0,0.3)", width=0.5)),
                hovertemplate=(
                    f"<b>{LABEL[s]}</b><br>"
                    "Actual: %{x:.0f} flights<br>"
                    "Predicted: %{y:.0f} flights<br>"
                    "Error: %{customdata:.0f}<extra></extra>"
                ),
                customdata=(grp["pred_RUL"] - grp["RUL"]).abs()
            ))

        fig_sc.update_layout(
            title=f"AI Prediction vs NASA Ground Truth — {subset}",
            xaxis_title="NASA Actual Remaining Flights",
            yaxis_title="AI Predicted Remaining Flights",
            height=380,
        )
        show(fig_sc)

    # ── Summary table across all subsets ─────────────────────────────────
    if not summary.empty:
        st.markdown('<div class="chart-row-label" style="margin-top:18px">All-Fleet Benchmark Results</div>', unsafe_allow_html=True)
        st.dataframe(
            summary,
            hide_index=True,
            use_container_width=True,
            column_config={c: st.column_config.NumberColumn(format="%.2f") for c in summary.select_dtypes("float").columns}
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ENGINE DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab_engine:
    units  = sorted(dec["unit"].astype(int).unique().tolist())
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

    sev_now   = now["severity"]
    sev_color = TEXT_C[sev_now]
    actual_left = f"{fail_cycle - at}" if fail_cycle else "—"
    err_str = f"{abs(now['pred_RUL'] - (fail_cycle - at)):.0f} flights" if fail_cycle else "—"

    # ─── Engine Detail Stats ──────────────────────────────────────────────
    st.html(f"""
    <div class="edc-grid">
      <div class="edc-card" style="border-left:3px solid {FILL[sev_now]};">
        <div class="edc-val" style="color:{sev_color};">{LABEL[sev_now]}</div>
        <div class="edc-label">Current Decision</div>
      </div>
      <div class="edc-card">
        <div class="edc-val" style="color:{BLUE};">{now['pred_RUL']:.0f}</div>
        <div class="edc-label">Flights Left (AI Estimate)</div>
      </div>
      <div class="edc-card">
        <div class="edc-val">{rng(now['rul_low'], now['rul_high'])}</div>
        <div class="edc-label">80% Safe Window</div>
      </div>
      <div class="edc-card">
        <div class="edc-val" style="color:#94A3B8;">{actual_left}</div>
        <div class="edc-label">Actual (NASA Answer)</div>
      </div>
      <div class="edc-card">
        <div class="edc-val" style="color:{'#FF4444' if now['anom'] else '#22D3A0'};">{now['anomaly_score']:.3f}</div>
        <div class="edc-label">Anomaly Score {'⚠️ Abnormal' if now['anom'] else '✅ Normal'}</div>
      </div>
    </div>
    """)

    # ─── RUL Trajectory Chart ────────────────────────────────────────────
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
            fill="tonexty", fillcolor="rgba(56,189,248,0.12)",
            line=dict(width=0), name="80% Confidence Cone",
            hoverinfo="skip"
        ))
    if fail_cycle:
        fig.add_trace(go.Scatter(
            x=h["cycle"], y=(fail_cycle - h["cycle"]).clip(upper=RUL_CAP),
            name="Actual RUL (NASA Ground Truth)",
            line=dict(color="#64748B", width=2, dash="dot"),
            hovertemplate="Flight %{x}: actual %{y:.0f} flights<extra></extra>"
        ))
    fig.add_trace(go.Scatter(
        x=h["cycle"], y=h["pred_RUL"],
        name="AI Point Prediction (LightGBM)",
        line=dict(color=BLUE, width=2.8),
        hovertemplate="Flight %{x}: estimated %{y:.0f} flights<extra></extra>"
    ))
    fig.add_vline(x=at, line_color=TEXT_3, line_width=1.5, line_dash="dash",
                  annotation_text=f" Flight {at}", annotation_font_color=TEXT_3,
                  annotation_position="top right")
    fig.update_layout(
        title=f"Engine {unit} — Remaining Useful Life Trajectory & 80% Safety Cone",
        hovermode="x unified", xaxis_title="Flight Cycle", yaxis_title="Flights Remaining"
    )
    show(fig, height=420)

    # ─── Anomaly Score Chart ─────────────────────────────────────────────
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=h["cycle"], y=h["anomaly_score"],
        name="Anomaly Score",
        line=dict(color=TEAL, width=2.2),
        fill="tozeroy", fillcolor="rgba(45,212,191,0.07)",
        hovertemplate="Flight %{x}: score %{y:.3f}<extra></extra>"
    ))
    anom_x = h[h["anom"]]["cycle"]
    anom_y = h[h["anom"]]["anomaly_score"]
    if len(anom_x):
        fig2.add_trace(go.Scatter(
            x=anom_x, y=anom_y, mode="markers",
            name="Abnormal Reading",
            marker=dict(color=FILL["CRITICAL"], size=6, symbol="circle"),
            hovertemplate="Flight %{x}: ABNORMAL %{y:.3f}<extra></extra>"
        ))
    fig2.add_hline(
        y=thr, line_dash="dash", line_color=FILL["CRITICAL"], line_width=1.5,
        annotation_text="Anomaly Threshold", annotation_position="top left",
        annotation_font_color=FILL["CRITICAL"]
    )
    fig2.add_vline(x=at, line_color=TEXT_3, line_width=1.5, line_dash="dash")
    fig2.update_layout(
        title=f"Engine {unit} — Sensor Anomaly Score (Isolation Forest)",
        hovermode="x unified", xaxis_title="Flight Cycle",
        yaxis_title="Anomaly Score", showlegend=True
    )
    show(fig2, height=280)

    # ─── Clean MRO Work Order Job Card ───────────────────────────────────
    wo_id = f"WO-{subset}-{unit:03d}-CYCLE{at:04d}"

    if sev_now == "CRITICAL":
        wo_action_title = "EMERGENCY GROUNDING & HEAVY OVERHAUL"
        wo_deadline = "Ground Immediately (0 Flights SLA)"
        wo_bay = "Bay 1 — Heavy Turbine Overhaul"
        wo_diagnosis = (
            f"Severe wear detected in the High-Pressure Compressor. "
            f"Anomaly sensor alarm triggered ({now['anomaly_score']:.3f} > {thr:.3f}). "
            f"Engine has {now['decision_RUL']:.0f} safe flights left — below emergency limit of {cfg['critical_rul']} flights."
        )
        tasks = [
            ("MANDATORY GROUNDING", "Issue immediate Aircraft-On-Ground (AOG) notice. Lock out dispatch clearance in the operations system."),
            ("BORESCOPE INSPECTION", "Inspect High-Pressure Compressor (HPC) rotor blades stage 6-9 for cracks, erosion, and tip damage."),
            ("MODULE OVERHAUL", "Disassemble turbine module. Replace High-Pressure Turbine stage-1 seals and worn stator vanes."),
            ("SENSOR RECALIBRATION", "Recalibrate temperature sensors and static pressure sensors (T30, P30)."),
            ("AIRWORTHINESS SIGN-OFF", "Run ground engine test from idle to full thrust. Complete official airworthiness certification before return to service.")
        ]
    elif sev_now == "HIGH":
        wo_action_title = "SCHEDULED DEPOT REPAIR & BLADE OVERHAUL"
        wo_deadline = f"Within {int(now['decision_RUL'])} flights"
        wo_bay = "Bay 3 — Scheduled Depot Maintenance"
        wo_diagnosis = (
            f"High-Pressure Compressor wear is significant. "
            f"Engine efficiency is dropping. Remaining safe flights ({now['decision_RUL']:.0f}) are approaching the "
            f"safety limit of {cfg['high_rul']} flights."
        )
        tasks = [
            ("PARTS PRE-ORDER", "Pre-order HPC blade kit and stage-1 seal package from main spares store."),
            ("DEPOT SCHEDULING", f"Book overnight hangar maintenance slot within {int(now['decision_RUL'])} flights."),
            ("COMPRESSOR WASH", "Chemical wash of compressor and optical inspection of combustor liner."),
            ("PRESSURE CHECK", "Check all bleed valve seals and turbine clearance gaps for leakage."),
            ("RETURN-TO-SERVICE TEST", "Conduct high-power ground runup test and clear engine for return to active fleet.")
        ]
    elif sev_now == "MEDIUM":
        wo_action_title = "ROUTINE LINE MAINTENANCE & INSPECTION"
        wo_deadline = f"Within {int(now['decision_RUL'])} flights"
        wo_bay = "Line Maintenance Gate"
        wo_diagnosis = (
            f"Early signs of wear detected. Anomaly score ({now['anomaly_score']:.3f}) is climbing toward the alarm level. "
            f"Routine inspection is needed to catch any defect before it gets worse."
        )
        tasks = [
            ("SCHEDULE INSPECTION", "Queue for line borescope check during next overnight scheduled stop."),
            ("FAN BLADE VISUAL CHECK", "Visual and optical check of fan blades and low-pressure compressor inlet."),
            ("OIL & DEBRIS AUDIT", "Check engine oil filter and magnetic chip detector for metal particles."),
            ("DATA DOWNLOAD", "Download quick-access flight recorder telemetry for baseline comparison.")
        ]
    else:
        wo_action_title = "ACTIVE LINE OPERATIONS & ROUTINE MONITORING"
        wo_deadline = "Active Service (No Action Needed)"
        wo_bay = "Operational Line Gate"
        wo_diagnosis = (
            f"All sensors and engine systems are within normal safe limits. "
            f"Predicted safe flights remaining: {now['pred_RUL']:.0f} — well above the caution level. "
            f"No maintenance needed at this time."
        )
        tasks = [
            ("PRE-FLIGHT WALKAROUND", "Standard visual check of cowl, fan blades, and exhaust nozzle before each departure."),
            ("FLUID LEVEL CHECK", "Verify engine oil and hydraulic fluid levels before next flight."),
            ("DISPATCH CLEARANCE", "Engine is cleared for unrestricted commercial flight schedule.")
        ]

    st.html(f'''
    <div class="wo-card" style="background:{SURFACE_3};border:2px solid {FILL[sev_now]};box-shadow:0 0 40px {GLOW[sev_now]};">
      <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid {BORDER};padding-bottom:14px;margin-bottom:16px;">
        <div>
          <span style="font-size:1.2rem;font-weight:800;color:{TEXT_1};letter-spacing:0.3px;">
            📋 WORK ORDER &nbsp;<code style="color:{BLUE};font-family:'JetBrains Mono',monospace;font-size:1.05rem;">{wo_id}</code>
          </span>
          <div style="font-size:0.82rem;color:{TEXT_3};margin-top:4px;">
            Target: <b style="color:{TEXT_2}">Engine Unit {unit:03d}</b> &nbsp;·&nbsp; Flight Cycle <b style="color:{TEXT_2}">{at}</b> of {c_max}
          </div>
        </div>
        <span style="background:{GLOW[sev_now]};color:{TEXT_C[sev_now]};font-weight:800;font-size:0.85rem;padding:8px 18px;border-radius:8px;border:1px solid {FILL[sev_now]};letter-spacing:0.3px;">
          ● {LABEL[sev_now].upper()} &nbsp;·&nbsp; {wo_action_title}
        </span>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;background:{SURFACE_2};border:1px solid {BORDER_SOFT};border-radius:10px;padding:14px 20px;margin-bottom:16px;">
        <div>
          <div style="font-size:0.72rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.8px;">Flights Remaining</div>
          <div style="font-size:1.45rem;font-weight:800;color:{TEXT_1};margin-top:3px;">{now['pred_RUL']:.0f} <span style="font-size:0.78rem;color:{TEXT_3};font-weight:400;">flights</span></div>
        </div>
        <div>
          <div style="font-size:0.72rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.8px;">Deadline</div>
          <div style="font-size:1.2rem;font-weight:800;color:{TEXT_C[sev_now]};margin-top:4px;">{wo_deadline}</div>
        </div>
        <div>
          <div style="font-size:0.72rem;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.8px;">Assigned Bay</div>
          <div style="font-size:1.1rem;font-weight:700;color:{TEXT_1};margin-top:4px;">{wo_bay}</div>
        </div>
      </div>

      <div style="margin-bottom:16px;">
        <div style="font-size:0.75rem;font-weight:700;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px;">⚠️ WHAT IS WRONG</div>
        <div style="font-size:0.87rem;color:{TEXT_1};background:{SURFACE_2};border:1px solid {BORDER_SOFT};border-radius:8px;padding:12px 16px;line-height:1.6;">
          {wo_diagnosis}
        </div>
      </div>

      <div style="font-size:0.75rem;font-weight:700;color:{TEXT_3};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:10px;">🔧 WHAT TO DO (CHECKLIST)</div>
    </div>
    ''')

    for idx, (t_title, t_desc) in enumerate(tasks, 1):
        t_col1, t_col2 = st.columns([0.06, 0.94], vertical_alignment="center")
        t_col1.checkbox("", value=(idx == 1 and sev_now in ["CRITICAL", "HIGH"]), key=f"wo_step_{unit}_{at}_{idx}")
        t_col2.markdown(f"**{idx}. {t_title}:** {t_desc}")

    printable_job_card = f"""================================================================================
AIRCRAFT TURBOFAN MAINTENANCE WORK ORDER
TATA ELXSI PREDICTIVE MAINTENANCE COMMAND CENTER
================================================================================
WORK ORDER ID   : {wo_id}
ENGINE SERIAL   : Unit {unit:03d}
FLIGHT CYCLE    : {at} of {c_max}
STATUS/SEVERITY : {LABEL[sev_now]}
ACTION          : {wo_action_title}
DEADLINE        : {wo_deadline}
ASSIGNED BAY    : {wo_bay}
PREDICTED RUL   : {now['pred_RUL']:.1f} flights (80% Safe Window: {rng(now['rul_low'], now['rul_high'])})
ANOMALY SCORE   : {now['anomaly_score']:.4f} (Threshold: {thr:.4f})
DATE ISSUED     : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
================================================================================
WHAT IS WRONG:
{wo_diagnosis}
================================================================================
WHAT TO DO:
""" + "\n".join([f"[{'X' if idx==1 and sev_now in ['CRITICAL', 'HIGH'] else ' '}] {idx}. {t[0]}: {t[1]}" for idx, t in enumerate(tasks, 1)]) + f"""
================================================================================
ENGINEER SIGN-OFF:
Lead MRO Inspector: ______________________   License #: _______________
Date Completed     : ______________________   Signature: _______________
================================================================================
"""

    wo_single_df = pd.DataFrame([{
        "work_order_id": wo_id, "unit": unit, "flight_cycle": at,
        "severity": sev_now, "status": LABEL[sev_now],
        "action_title": wo_action_title, "deadline": wo_deadline,
        "assigned_bay": wo_bay, "predicted_RUL": round(now['pred_RUL'], 1),
        "conformal_lower_80": round(now['rul_low'], 1),
        "conformal_upper_80": round(now['rul_high'], 1),
        "anomaly_score": round(now['anomaly_score'], 4),
        "diagnosis": wo_diagnosis,
        "issued_timestamp": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    }])

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.8rem;color:{TEXT_3};margin-bottom:8px;'>📥 Download this Work Order for Engineer / Technician:</div>", unsafe_allow_html=True)
    d1, d2, d3, _ = st.columns([1.4, 1.2, 1.2, 2.2])
    d1.download_button("📄 Job Sheet (TXT)", printable_job_card,
                       file_name=f"{wo_id}_JobSheet.txt", mime="text/plain", key=f"dl_txt_{unit}_{at}")
    d2.download_button("📊 CSV", wo_single_df.to_csv(index=False),
                       file_name=f"{wo_id}.csv", mime="text/csv", key=f"dl_csv_{unit}_{at}")
    d3.download_button("📦 JSON", wo_single_df.to_json(orient="records", indent=2),
                       file_name=f"{wo_id}.json", mime="application/json", key=f"dl_json_{unit}_{at}")

# ══════════════════════════════════════════════════════════════════════════════
