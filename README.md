# Jet Engine Health Monitor & Predictive Maintenance Fleet Dashboard

> **Tata Elxsi Teliport Season 4 — Case Study 1: Predictive Maintenance (ACTG)**  
> *Closed-Loop Predictive Maintenance System for Turbofan Fleets*  
> Author: **Ashit**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tata-elxsi-engine-health.streamlit.app)
[![NASA C-MAPSS](https://img.shields.io/badge/Dataset-NASA%20C--MAPSS-blue.svg)](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)

---

## Overview

This interactive command center demonstrates an end-to-end predictive maintenance system evaluated across all 4 subsets of the **NASA C-MAPSS benchmark (FD001–FD004)**, comprising **707 test engines**.

The platform moves from raw high-frequency telemetry to automated, audited maintenance work orders with **zero critical engines missed**.

### Key Highlights
- **Fleet Matrix**: Interactive visual board of all test engines color-coded by operational status (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `HUMAN_REVIEW`).
- **Pessimistic Decision Policy**: Evaluates the calibrated **10% lower quantile bound** rather than a raw point estimate, cutting urgent misclassifications from $21.7\%$ to $0.0\%$.
- **Dual-Model Safety Verification**: Unsupervised **Isolation Forest** corroborates the supervised **LightGBM 5-seed ensemble**. Conflicting predictions automatically route to human aerospace engineers (`HUMAN_REVIEW`).
- **Autonomous Work Orders**: One-click download of enterprise-ready `.csv` and `.json` maintenance work orders with SLAs and flight deadlines.
- **Flight-by-Flight Replay Slider**: Scrub through an engine's operational cycles to view multi-sensor degradation traces, anomaly score spikes, and the expanding/tightening uncertainty cone.
- **MLOps Retraining History**: Full MLflow model tournament ledger and live demonstration of sensor drift-gated continuous retraining (Validation RMSE improved from $9.01 \to 8.63$).

---

## Local Setup & Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/engine-health-monitor.git
cd engine-health-monitor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit dashboard
streamlit run dashboard.py
```

---

## Repository Structure

```text
├── dashboard.py                # Main Streamlit command center application
├── requirements.txt            # Streamlit, Plotly, Pandas dependencies
├── .streamlit/
│   └── config.toml             # Custom UI theme configuration
├── dashboard_data/             # Precomputed pipeline artifacts & evaluations
│   ├── summary_all_subsets.csv # Benchmark metrics across all 4 NASA datasets
│   ├── config_FD00*.json       # Operational thresholds & calibration parameters
│   ├── decisions_FD00*.csv     # Per-engine forecasts, quantile ranges & decisions
│   ├── engine_history_FD00*.csv# Full sensor traces & anomaly histories
│   ├── mlflow_runs_FD00*.csv   # Experiment tracking ledgers
│   └── work_orders_FD00*.csv   # Generated maintenance work orders
└── README.md                   # System documentation & deployment guide
```
