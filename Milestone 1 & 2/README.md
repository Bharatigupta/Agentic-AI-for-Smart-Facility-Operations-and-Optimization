# Agentic FacilityOps AI Platform — Milestone 1 & 2 Demo

This is a **working** implementation of:

- **Milestone 1 (Weeks 1–2): Energy Intelligence & Monitoring** — `agents/energy_agent.py`
- **Milestone 2 (Weeks 3–4): Predictive Maintenance System** — `agents/maintenance_agent.py`

It's a real Flask app backed by SQLite, with a simulated IoT/utility data
stream so you can demo it live without needing actual sensor hardware.

## What each agent actually does

### Energy Agent (Milestone 1)
- Ingests simulated utility/IoT readings every cycle
- Computes KPIs: total energy (MWh), cost savings, efficiency score, carbon reduction %
- Breaks down consumption by HVAC / Lighting / Equipment / Other
- Detects off-hours energy wastage
- Analyzes HVAC load and flags underperformance
- Optimizes lighting schedules based on time of day
- Forecasts demand for the next 6 hours
- Generates plain-English savings recommendations

### Maintenance Agent (Milestone 2)
- Simulates sensor cycles (temperature, vibration) for 14 assets across the
  facility (HVAC units, chillers, generators, pumps, transformers, etc.)
- Computes a health score per asset and buckets them into
  Excellent / Good / Warning / Critical
- Runs z-score anomaly detection against each asset's recent history
- Predicts risk level and days-to-maintenance per asset
- **Automatically opens a maintenance work order** when an asset's risk
  becomes High/Critical (no duplicate tickets)
- Tracks asset age, runtime hours, and remaining lifecycle %

Every ~12 seconds the background simulator "ticks" — pushes new sensor data
in, so if you leave the dashboard open for a minute or two you'll watch
health scores drift, anomalies appear, and work orders get created live.
That's the best moment to screen-record for your presentation.

## How to run it

```bash
cd facilityops
pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser.

The database (`facilityops.db`) is created and auto-seeded on first run
with one demo facility ("Corporate Tower A") and 14 assets, plus 24 hours
of backfilled energy history so the charts aren't empty on first load.

To reset the demo data, just delete `facilityops.db` and restart the app.

## What you'll see on screen

**Tab 1 — Energy Intelligence (Milestone 1)**
- KPI cards: Total Energy, Cost Savings, Efficiency Score, Carbon Reduction
- 24-hour electricity usage trend line
- Energy distribution bars (HVAC / Lighting / Equipment / Other)
- HVAC efficiency status
- 6-hour demand forecast bar chart
- Live AI-generated recommendations list

**Tab 2 — Predictive Maintenance (Milestone 2)**
- KPI cards: Assets Monitored, Maintenance Tickets, Predicted Failures, Downtime Reduction
- Equipment health distribution bars
- Failure risk prediction table (per asset, with risk badges)
- Auto-generated work orders table
- Live abnormal-behavior/anomaly alerts

## Project structure

```
facilityops/
├── app.py                      # Flask app + API routes + background simulation loop
├── agents/
│   ├── energy_agent.py         # Milestone 1 agent logic
│   └── maintenance_agent.py    # Milestone 2 agent logic
├── data/
│   ├── database.py             # SQLite schema (facilities, assets, energy_usage,
│   │                            #   asset_readings, maintenance_records, alerts)
│   └── simulator.py            # Seeds demo data + advances the live simulation
├── templates/
│   └── dashboard.html          # Two-tab live dashboard (Chart.js)
└── requirements.txt
```

## Extending toward Milestone 3 & 4

The database schema and API pattern here already anticipate the Occupancy
Agent, Security Agent, and Cost Optimization Agent from the full project
plan — you'd add `occupancy_records`, `security_events`, and `cost_reports`
tables (already sketched in the project's ER diagram) and new agent
classes following the same structure as `energy_agent.py` /
`maintenance_agent.py`.
