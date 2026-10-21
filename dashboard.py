"""
Engine health monitor - Streamlit dashboard for the C-MAPSS predictive maintenance pipeline (v3).

Folder layout:
    engine-dashboard/
        dashboard.py
        requirements.txt
        .streamlit/config.toml
        dashboard_data/      <- unzip dashboard_data.zip from Kaggle here

Run:
    pip install -r requirements.txt
    streamlit run dashboard.py
"""
import glob
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
from packaging.version import Version

st.set_page_config(page_title="Engine health monitor", page_icon="✈️", layout="wide",
                   initial_sidebar_state="collapsed")

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_data")
RUL_CAP, PERSIST = 125, 5

# ----------------------------------------------------------------------------- design tokens
INK, INK_2, INK_3 = "#1B2430", "#5B6675", "#8A94A3"
PAGE, PANEL, RULE, GRID = "#EEF1F4", "#FFFFFF", "#D5DBE2", "#E6EAEF"
ACCENT, ACCENT_SOFT = "#1F5FBF", "#C9DAF3"

# Status: fill (marks) and text (labels) are separate tokens; healthy recedes on purpose
SEV = {
    "CRITICAL":     dict(label="Ground now",      fill="#D03B3B", text="#B42318"),
    "HIGH":         dict(label="Repair soon",     fill="#EC835A", text="#B54708"),
    "MEDIUM":       dict(label="Inspect",         fill="#FAB219", text="#8A6100"),
    "HUMAN_REVIEW": dict(label="Engineer review", fill="#6250D6", text="#5140C2"),
    "LOW":          dict(label="Healthy",         fill="#C5D6CA", text="#2E6B3E"),
}
ORDER = list(SEV)
PRIORITY = {s: i for i, s in enumerate(ORDER)}
LABEL = {k: v["label"] for k, v in SEV.items()}
FILL = {k: v["fill"] for k, v in SEV.items()}
TEXT = {k: v["text"] for k, v in SEV.items()}
SEQ_BLUE = ["#EEF3FB", "#C9DAF3", "#8DB2E6", "#4F86D3", "#1F5FBF", "#174A96", "#103670"]

pio.templates["ehm"] = go.layout.Template(layout=dict(
    font=dict(family="Barlow, Segoe UI, sans-serif", color=INK, size=13),
    title=dict(font=dict(family="Barlow Semi Condensed, Barlow, sans-serif", size=16, color=INK), x=0, xanchor="left"),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=PANEL, colorway=[ACCENT],
    xaxis=dict(gridcolor=GRID, linecolor=RULE, zeroline=False, ticks="", automargin=True, title_font=dict(color=INK_2)),
    yaxis=dict(gridcolor=GRID, linecolor=RULE, zeroline=False, ticks="", automargin=True, title_font=dict(color=INK_2)),
    hoverlabel=dict(bgcolor=PANEL, bordercolor=RULE, font=dict(family="Barlow, sans-serif", color=INK, size=13)),
    legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom", font=dict(color=INK_2)),
    margin=dict(l=64, r=16, t=60, b=56),
))
pio.templates.default = "ehm"

CSS = f"""
<style>@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600&display=swap');</style>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Semi+Condensed:wght@500;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stMarkdown, .stText, button, input, label, p, li, td, th {{
    font-family: 'Barlow', 'Segoe UI', sans-serif;
}}
.stApp {{ background: {PAGE}; }}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
#MainMenu, footer, [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}
.block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }}
h1, h2, h3 {{ font-family: 'Barlow Semi Condensed', 'Barlow', sans-serif !important; color: {INK}; letter-spacing: 0; }}

/* panels */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {{
    background: {PANEL}; border-color: {RULE} !important; border-radius: 6px;
}}

/* header */
.ehm-title {{ font-family: 'Barlow Semi Condensed', sans-serif !important; font-weight: 600 !important;
              font-size: 2.1rem !important; color: {INK}; line-height: 1.1 !important; margin: 0 0 2px 0 !important; }}
.ehm-sub {{ color: {INK_2}; font-size: 0.95rem; margin-top: 4px; }}
.ehm-status {{ font-size: 1.15rem; color: {INK}; margin: 1.2rem 0 0.8rem; max-width: 70ch; }}
.ehm-status b {{ font-weight: 600; }}

/* fleet board */
.board {{ display: flex; flex-wrap: wrap; gap: 3px; padding: 4px 0 2px; }}
.tile {{ width: 15px; height: 22px; border-radius: 2px; display: inline-block; }}
.tile:hover {{ outline: 2px solid {INK}; outline-offset: 1px; }}
.board-key {{ display: flex; flex-wrap: wrap; gap: 6px 28px; margin-top: 14px; }}
.key {{ display: flex; align-items: baseline; gap: 8px; color: {INK_2}; font-size: 0.95rem; }}
.key .sw {{ width: 12px; height: 12px; border-radius: 2px; display: inline-block; align-self: center; }}
.key .n {{ font-family: 'Barlow Semi Condensed', sans-serif; font-size: 1.5rem; font-weight: 600; color: {INK}; }}

/* stat strip */
.stats {{ display: flex; flex-wrap: wrap; gap: 8px 40px; margin: 4px 0 6px; }}
.stat .v {{ font-family: 'Barlow Semi Condensed', sans-serif; font-size: 1.7rem; font-weight: 600; color: {INK};
            line-height: 1.15; font-variant-numeric: tabular-nums; }}
.stat .l {{ color: {INK_2}; font-size: 0.9rem; }}
.note {{ color: {INK_2}; font-size: 0.92rem; max-width: 80ch; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 26px; border-bottom: 1px solid {RULE}; }}
.stTabs [data-baseweb="tab"] {{ font-size: 1rem; padding: 8px 0; color: {INK_2}; }}
.stTabs [aria-selected="true"] {{ color: {INK}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {ACCENT}; }}
</style>
"""
# Streamlit ends an HTML block at a blank line, so drop blank lines and comments
st.markdown("\n".join(l for l in CSS.splitlines() if l.strip() and not l.strip().startswith("/*")),
            unsafe_allow_html=True)

NEW_ST = Version(st.__version__) >= Version("1.50")


def show(fig, where=st, height=None):
    if height:
        fig.update_layout(height=height)
    if NEW_ST:
        where.plotly_chart(fig, width="stretch", theme=None)
    else:
        where.plotly_chart(fig, use_container_width=True, theme=None)


def stats_html(items):
    cells = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>' for l, v in items)
    return f'<div class="stats">{cells}</div>'


def panel():
    return st.container(border=True)


# ----------------------------------------------------------------------------- data
subsets = sorted(os.path.basename(p)[len("decisions_"):-len(".csv")]
                 for p in glob.glob(os.path.join(DATA, "decisions_*.csv")))
if not subsets:
    st.error(f"No pipeline output found in {DATA}. Unzip dashboard_data.zip from Kaggle into a folder "
             "named dashboard_data next to dashboard.py, with the CSV files directly inside it.")
    st.stop()


@st.cache_data
def load(subset):
    def csv(name):
        p = os.path.join(DATA, name)
        return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
    with open(os.path.join(DATA, f"config_{subset}.json")) as f:
        cfg = json.load(f)
    dec = csv(f"decisions_{subset}.csv")
    hist = csv(f"engine_history_{subset}.csv")
    for df in (dec, hist):                      # v2 exports have no range: fall back to the point estimate
        if not df.empty:
            for c in ["rul_low", "rul_high", "decision_RUL"]:
                if c not in df.columns:
                    df[c] = df["pred_RUL"]
    return dict(dec=dec, hist=hist, wo=csv(f"work_orders_{subset}.csv"), runs=csv(f"mlflow_runs_{subset}.csv"),
                summary=csv("summary_all_subsets.csv"), cfg=cfg)


def triage(rul, anomaly, cfg):
    """Same rules as the pipeline's Triage Agent."""
    if rul <= cfg["critical_rul"]:
        return "CRITICAL"
    if rul <= cfg["high_rul"]:
        return "HIGH"
    if anomaly and rul > cfg["long_life_rul"]:
        return "HUMAN_REVIEW"
    if rul <= cfg["medium_rul"]:
        return "MEDIUM"
    return "LOW"


def true_severity(rul, cfg):
    return ("CRITICAL" if rul <= cfg["critical_rul"] else "HIGH" if rul <= cfg["high_rul"]
            else "MEDIUM" if rul <= cfg["medium_rul"] else "LOW")


def rng(lo, hi):
    return f"{lo:.0f}–{hi:.0f}"


# ----------------------------------------------------------------------------- header
left, right = st.columns([3, 2], vertical_alignment="bottom")
with left:
    st.markdown('<div class="ehm-title">Engine health monitor</div>'
                '<p class="ehm-sub">NASA C-MAPSS test fleet (simulated turbofan data). '
                'Remaining life in flights; a flight is one engine cycle.</p>', unsafe_allow_html=True)
with right:
    subset = st.radio("Dataset", subsets, horizontal=True, label_visibility="collapsed")

D = load(subset)
dec, hist, wo, runs, summary, cfg = D["dec"], D["hist"], D["wo"], D["runs"], D["summary"], D["cfg"]
dec = dec.assign(priority=dec["severity"].map(PRIORITY)).sort_values(["priority", "decision_RUL"])
has_truth = "RUL" in dec.columns
has_range = not (dec["rul_low"] == dec["pred_RUL"]).all()
counts = dec["severity"].value_counts()

# ----------------------------------------------------------------------------- status + fleet board
n_ground, n_repair = int(counts.get("CRITICAL", 0)), int(counts.get("HIGH", 0))
n_inspect, n_review = int(counts.get("MEDIUM", 0)), int(counts.get("HUMAN_REVIEW", 0))
sentence = (f"<b>{n_ground}</b> of {len(dec)} engines should be grounded now and <b>{n_repair}</b> "
            f"need repair within {cfg['high_rul']} flights. {n_inspect} are due an inspection"
            + (f", and {n_review} {'is' if n_review == 1 else 'are'} waiting for an engineer." if n_review else "."))
st.markdown(f'<p class="ehm-status">{sentence}</p>', unsafe_allow_html=True)

with panel():
    tiles = "".join(
        f'<span class="tile" style="background:{FILL[r.severity]}" '
        f'title="Engine {int(r.unit)}: {LABEL[r.severity]}. About {r.pred_RUL:.0f} flights left '
        f'(range {rng(r.rul_low, r.rul_high)})."></span>'
        for r in dec.itertuples())
    keys = "".join(
        f'<span class="key"><span class="sw" style="background:{FILL[s]}"></span>'
        f'<span class="n">{int(counts.get(s, 0))}</span>{LABEL[s]}</span>' for s in ORDER)
    st.markdown(f'<div class="board">{tiles}</div><div class="board-key">{keys}</div>', unsafe_allow_html=True)
    st.caption("Each tile is one engine, most urgent first. Hover a tile for its forecast.")

tab_list, tab_engine, tab_val, tab_model = st.tabs(
    ["Action list", "Engine detail", "Validation", "Model and retraining"])

# ----------------------------------------------------------------------------- action list
with tab_list:
    act = dec[dec["severity"] != "LOW"].copy()
    if act.empty:
        st.info("Every engine is healthy. Nothing to schedule.")
    else:
        options = [s for s in ORDER if s != "LOW"]
        pick = st.multiselect("Show", options, default=options, format_func=lambda s: LABEL[s])
        act = act[act["severity"].isin(pick)]
        ids = dict(zip(wo["unit"], wo["work_order_id"])) if not wo.empty else {}
        table = pd.DataFrame({
            "Engine": act["unit"].astype(int),
            "Status": act["severity"].map(LABEL),
            "Flights left": act["pred_RUL"].round(),
            "Likely range": [rng(a, b) for a, b in zip(act["rul_low"], act["rul_high"])],
            "Planned on": act["decision_RUL"].round(),
            "Action": act["action"],
            "Engineer check": act["needs_human"].astype(bool),
            "Work order": act["unit"].map(ids).fillna("-"),
        })
        sev_codes = act["severity"].values

        def colour_status(col):
            return [f"color: {TEXT[s]}; font-weight: 600" for s in sev_codes]

        styled = table.style.apply(colour_status, subset=["Status"])
        st.dataframe(styled, hide_index=True, height=min(38 * (len(table) + 1) + 4, 620), column_config={
            "Flights left": st.column_config.ProgressColumn("Flights left (best estimate)", min_value=0,
                                                            max_value=RUL_CAP, format="%d"),
            "Planned on": st.column_config.NumberColumn(
                "Planned on", format="%d",
                help="The pessimistic end of the range. The agent decides on this value, so an "
                     "uncertain engine is handled early rather than late."),
            "Engineer check": st.column_config.CheckboxColumn("Engineer check"),
        })
        c1, c2, _ = st.columns([1, 1, 4])
        if not wo.empty:
            c1.download_button("Download CSV", wo.to_csv(index=False),
                               file_name=f"work_orders_{subset}.csv", mime="text/csv")
            c2.download_button("Download JSON", wo.to_json(orient="records", indent=2),
                               file_name=f"work_orders_{subset}.json", mime="application/json")

# ----------------------------------------------------------------------------- engine detail
with tab_engine:
    units = dec["unit"].astype(int).tolist()
    sev_of = dict(zip(dec["unit"].astype(int), dec["severity"]))
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    unit = c1.selectbox("Engine", units, format_func=lambda u: f"Engine {u}  ({LABEL[sev_of[u]]})")
    row = dec[dec["unit"] == unit].iloc[0]

    h = hist[hist["unit"] == unit].sort_values("cycle").reset_index(drop=True)
    thr = cfg["anomaly_threshold"]
    h["anom"] = h["anomaly_score"] > thr
    h["persist"] = h["anom"].astype(int).rolling(PERSIST, min_periods=1).min().eq(1)
    h["severity"] = [triage(round(r), a, cfg) for r, a in zip(h["decision_RUL"], h["persist"])]
    fail_cycle = int(row["cycle"] + row["RUL"]) if has_truth else None

    c_min, c_max = int(h["cycle"].min()), int(h["cycle"].max())
    at = c2.slider("Replay to flight", c_min, c_max, c_max,
                   help="Move back in time to see what the system knew and decided at that point.") \
        if c_max > c_min else c_max
    now = h[h["cycle"] == at].iloc[0]

    with panel():
        sev_now = now["severity"]
        st.markdown(stats_html([
            ("Decision at this flight",
             f'<span style="color:{TEXT[sev_now]}">{LABEL[sev_now]}</span>'),
            ("Flights left, best estimate", f"{now['pred_RUL']:.0f}"),
            ("Likely range", rng(now["rul_low"], now["rul_high"])),
            ("Actual flights left (NASA answer)", f"{fail_cycle - at}" if fail_cycle else "unknown"),
            ("Anomaly score", f"{now['anomaly_score']:.3f}" + (" (abnormal)" if now["anom"] else "")),
        ]), unsafe_allow_html=True)

        fig = go.Figure()
        for lo, hi, s in [(0, cfg["critical_rul"], "CRITICAL"), (cfg["critical_rul"], cfg["high_rul"], "HIGH"),
                          (cfg["high_rul"], cfg["medium_rul"], "MEDIUM")]:
            fig.add_hrect(y0=lo, y1=hi, fillcolor=FILL[s], opacity=0.07, line_width=0)
        if has_range:
            fig.add_trace(go.Scatter(x=h["cycle"], y=h["rul_high"], line=dict(width=0), showlegend=False,
                                     hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=h["cycle"], y=h["rul_low"], fill="tonexty", fillcolor=ACCENT_SOFT,
                                     line=dict(width=0), name="Likely range (80%)", hoverinfo="skip"))
        if fail_cycle:
            fig.add_trace(go.Scatter(x=h["cycle"], y=(fail_cycle - h["cycle"]).clip(upper=RUL_CAP),
                                     name="Actual (NASA answer)", line=dict(color=INK_3, width=2, dash="dash"),
                                     hovertemplate="Flight %{x}: actual %{y:.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=h["cycle"], y=h["pred_RUL"], name="Best estimate",
                                 line=dict(color=ACCENT, width=2),
                                 hovertemplate="Flight %{x}: estimate %{y:.0f}<extra></extra>"))
        fig.add_vline(x=at, line_color=INK_2, line_width=1)
        fig.update_layout(title="Remaining life over this engine's history", hovermode="x unified",
                          xaxis_title="Flight", yaxis_title="Flights left")
        show(fig, height=380)

        fig = go.Figure(go.Scatter(x=h["cycle"], y=h["anomaly_score"], name="Anomaly score",
                                   line=dict(color=ACCENT, width=2),
                                   hovertemplate="Flight %{x}: %{y:.3f}<extra></extra>"))
        fig.add_hline(y=thr, line_dash="dash", line_color=SEV["CRITICAL"]["fill"], line_width=1,
                      annotation_text="abnormal above this line", annotation_position="top left",
                      annotation_font_color=INK_2)
        fig.add_vline(x=at, line_color=INK_2, line_width=1)
        fig.update_layout(title="How unusual the sensors look", hovermode="x unified",
                          xaxis_title="Flight", yaxis_title="Anomaly score", showlegend=False)
        show(fig, height=260)

    first = h[h["severity"] != "LOW"].head(1)
    if not first.empty:
        c0 = int(first["cycle"].iloc[0])
        msg = f"The first work order for this engine would have been raised at flight {c0} ({LABEL[first['severity'].iloc[0]]})"
        msg += f", {fail_cycle - c0} flights before failure." if fail_cycle else "."
        st.markdown(f'<p class="note">{msg}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="note"><b>Current decision:</b> {row["action"]}. {row["reason"]}.</p>',
                unsafe_allow_html=True)
    if not wo.empty and unit in wo["unit"].values:
        with st.expander("Work order"):
            st.json(wo[wo["unit"] == unit].iloc[0].dropna().to_dict())

# ----------------------------------------------------------------------------- validation
with tab_val:
    if not has_truth:
        st.info("This export has no answer key, so predictions can't be checked.")
    else:
        st.markdown('<p class="note">Each test engine\'s latest prediction is compared with NASA\'s answer file '
                    f'(RUL_{subset}.txt). The model never saw these answers while it was trained or tuned.</p>',
                    unsafe_allow_html=True)
        y_true = dec["RUL"].values
        y_cap = np.minimum(y_true, RUL_CAP)
        err = dec["pred_RUL"].values - y_cap
        truth = np.array([true_severity(r, cfg) for r in y_true])
        level = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "HUMAN_REVIEW": 1, "LOW": 0}
        t_lv = np.array([level[t] for t in truth])
        d_lv = np.array([level[d] for d in dec["severity"]])
        urgent = t_lv >= 2
        covered = ((y_cap >= dec["rul_low"].values) & (y_cap <= dec["rul_high"].values)).mean()
        missed = int(((y_true <= cfg["critical_rul"]) & ~dec["severity"].isin(["CRITICAL", "HIGH"])).sum())

        with panel():
            st.markdown(stats_html([
                ("Average error", f"{np.abs(err).mean():.1f} flights"),
                ("RMSE", f"{np.sqrt((err ** 2).mean()):.2f}"),
                ("Range contains the answer", f"{covered:.0%}" if has_range else "no range"),
                ("Urgent engines rated too low", f"{int((d_lv < t_lv)[urgent].sum())} of {int(urgent.sum())}"),
                ("Critical engines missed", f"{missed}"),
            ]), unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1, panel():
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[0, RUL_CAP, max(y_true.max(), RUL_CAP) + 5], y=[0, RUL_CAP, RUL_CAP],
                                     mode="lines", name="Perfect (capped at 125)", hoverinfo="skip",
                                     line=dict(color=INK_3, dash="dash", width=1.5)))
            fig.add_trace(go.Scatter(
                x=y_true, y=dec["pred_RUL"], mode="markers", name="Test engine",
                error_y=dict(type="data", symmetric=False, array=dec["rul_high"] - dec["pred_RUL"],
                             arrayminus=dec["pred_RUL"] - dec["rul_low"], color=ACCENT_SOFT, thickness=1.2,
                             width=0) if has_range else None,
                marker=dict(color=ACCENT, size=7, line=dict(color=PANEL, width=1)),
                customdata=np.stack([dec["unit"], dec["rul_low"], dec["rul_high"]], axis=1),
                hovertemplate="Engine %{customdata[0]}<br>Actual %{x}<br>Estimate %{y:.0f} "
                              "(range %{customdata[1]:.0f}–%{customdata[2]:.0f})<extra></extra>"))
            fig.update_layout(title="Estimate and range vs actual remaining life",
                              xaxis_title="Actual flights left (NASA answer)", yaxis_title="Estimated flights left")
            show(fig, height=380)

        with c2, panel():
            zones = pd.cut(y_true, [-1, 25, 50, 75, 125, 100000], labels=["0–25", "26–50", "51–75", "76–125", "over 125"])
            z = (pd.DataFrame({"zone": zones, "e": np.abs(err)}).groupby("zone", observed=False)
                 .agg(mae=("e", "mean"), n=("e", "size")).reset_index().fillna(0))
            fig = go.Figure(go.Bar(x=z["zone"].astype(str), y=z["mae"], marker_color=ACCENT,
                                   text=z["mae"].round(1), textposition="outside", cliponaxis=False,
                                   customdata=z["n"],
                                   hovertemplate="%{x} flights left<br>Average error %{y:.1f}<br>"
                                                 "%{customdata} engines<extra></extra>"))
            fig.update_layout(title="Average error by distance to failure", barcornerradius=3,
                              xaxis_title="Actual flights left", yaxis_title="Average error (flights)")
            show(fig, height=380)

        c1, c2 = st.columns(2)
        with c1, panel():
            fig = go.Figure(go.Histogram(x=err, nbinsx=30, marker_color=ACCENT,
                                         hovertemplate="Error %{x}<br>%{y} engines<extra></extra>"))
            fig.add_vline(x=0, line_color=INK_2, line_width=1)
            fig.add_annotation(x=0, y=1.04, yref="paper", text="too early (safe)  ", xanchor="right",
                               showarrow=False, font=dict(color=INK_2))
            fig.add_annotation(x=0, y=1.04, yref="paper", text="  too late (risky)", xanchor="left",
                               showarrow=False, font=dict(color=INK_2))
            fig.update_layout(title="Estimate minus actual", bargap=0.08,
                              xaxis_title="Flights", yaxis_title="Engines")
            show(fig, height=340)

        with c2, panel():
            cols = ["CRITICAL", "HIGH", "MEDIUM", "HUMAN_REVIEW", "LOW"]
            rows = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            cm = pd.crosstab(pd.Series(truth, name="t"), dec["severity"].reset_index(drop=True).rename("d")) \
                .reindex(index=rows, columns=cols, fill_value=0)
            fig = go.Figure(go.Heatmap(z=cm.values, x=[LABEL[c] for c in cols], y=[LABEL[r] for r in rows],
                                       colorscale=[[i / 6, c] for i, c in enumerate(SEQ_BLUE)], showscale=False,
                                       text=cm.values, texttemplate="%{text}", xgap=2, ygap=2,
                                       hovertemplate="Should be: %{y}<br>Agent: %{x}<br>%{z} engines<extra></extra>"))
            fig.update_layout(title="Agent decision vs correct decision", plot_bgcolor=PANEL,
                              xaxis_title="Agent decided", yaxis=dict(title="Should have been", autorange="reversed"))
            show(fig, height=340)

        if not summary.empty:
            st.subheader("All four datasets, same pipeline")
            keep = {"subset": "Dataset", "trained_with": "Trained with", "test_engines": "Test engines",
                    "test_rmse": "RMSE", "test_mae": "Average error", "nasa_score": "NASA score",
                    "test_range_coverage": "Range contains answer", "urgent_underrated": "Urgent rated too low (v2 → v3)",
                    "critical_missed": "Critical missed", "work_orders": "Work orders"}
            tbl = summary[[c for c in keep if c in summary.columns]].rename(columns=keep)
            st.dataframe(tbl, hide_index=True)

# ----------------------------------------------------------------------------- model & retraining
with tab_model:
    c1, c2 = st.columns(2)
    if not summary.empty and "test_rmse" in summary.columns:
        with c1, panel():
            fig = go.Figure(go.Bar(x=summary["subset"], y=summary["test_rmse"], marker_color=ACCENT,
                                   text=summary["test_rmse"].round(2), textposition="outside", cliponaxis=False,
                                   hovertemplate="%{x}: RMSE %{y:.2f}<extra></extra>"))
            fig.update_layout(title="Test RMSE per dataset", barcornerradius=3, yaxis_title="RMSE (flights)")
            show(fig, height=340)

    if not runs.empty and "metrics.test_rmse" in runs.columns:
        journey = runs[runs["metrics.test_rmse"].notna() & runs["tags.mlflow.runName"].str.match(r"^\d_")] \
            .sort_values("tags.mlflow.runName")
        if len(journey) > 1:
            with c2, panel():
                names = journey["tags.mlflow.runName"].str.replace(r"^\d_", "", regex=True).str.replace("_", " ")
                fig = go.Figure(go.Bar(x=names, y=journey["metrics.test_rmse"], marker_color=ACCENT,
                                       text=journey["metrics.test_rmse"].round(1), textposition="outside",
                                       cliponaxis=False, hovertemplate="%{x}<br>RMSE %{y:.2f}<extra></extra>"))
                fig.update_layout(title="How the model improved (FD001, from MLflow)", barcornerradius=3,
                                  yaxis_title="RMSE (flights)")
                show(fig, height=340)

    if not runs.empty and "metrics.val_rmse" in runs.columns and runs["metrics.val_rmse"].notna().any():
        st.subheader("Retraining history")
        st.markdown('<p class="note">When new engine data arrives, a challenger model is trained and compared '
                    'with the current champion on the same validation engines. It replaces the champion only '
                    'if it is more accurate.</p>', unsafe_allow_html=True)
        rt = runs[runs["metrics.val_rmse"].notna()].sort_values("start_time")
        cols = {"start_time": "Time", "tags.mlflow.runName": "Run", "tags.stage": "Result",
                "params.n_train_engines": "Training engines", "metrics.val_rmse": "Validation RMSE",
                "metrics.max_sensor_drift": "Largest sensor drift"}
        st.dataframe(rt[[c for c in cols if c in rt.columns]].rename(columns=cols), hide_index=True,
                     column_config={"Validation RMSE": st.column_config.NumberColumn(format="%.2f"),
                                    "Largest sensor drift": st.column_config.NumberColumn(format="%.2f")})
    elif subset != "FD001":
        st.markdown('<p class="note">The retraining demo runs on FD001. Select FD001 to see it.</p>',
                    unsafe_allow_html=True)

    st.markdown(f'<p class="note">Settings for {subset}: trained together with {cfg.get("trained_with") or "no partner"}, '
                f'safety margin {cfg.get("safety_margin", 0)} flights, decision rule '
                f'"{cfg.get("decision_policy", "point estimate")}", anomaly threshold {cfg["anomaly_threshold"]:.3f}.</p>',
                unsafe_allow_html=True)
