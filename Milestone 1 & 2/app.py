import threading
import time

from flask import Flask, jsonify, render_template

from data.database import init_db
from data import simulator
from agents.energy_agent import EnergyAgent
from agents.maintenance_agent import MaintenanceAgent

app = Flask(__name__)
FACILITY_ID = 1
TICK_SECONDS = 12  # how often the simulated IoT stream produces a new reading


def background_loop():
    while True:
        time.sleep(TICK_SECONDS)
        try:
            simulator.tick(FACILITY_ID)
        except Exception as e:
            print("simulation tick error:", e)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# ------------------------- Milestone 1: Energy Agent -------------------------

@app.route("/api/energy/kpis")
def energy_kpis():
    return jsonify(EnergyAgent(FACILITY_ID).compute_kpis())


@app.route("/api/energy/recommendations")
def energy_recommendations():
    return jsonify(EnergyAgent(FACILITY_ID).generate_recommendations())


@app.route("/api/energy/forecast")
def energy_forecast():
    return jsonify(EnergyAgent(FACILITY_ID).forecast_demand())


@app.route("/api/energy/wastage")
def energy_wastage():
    return jsonify(EnergyAgent(FACILITY_ID).detect_wastage())


@app.route("/api/energy/hvac")
def energy_hvac():
    return jsonify(EnergyAgent(FACILITY_ID).analyze_hvac_efficiency())


@app.route("/api/energy/trend")
def energy_trend():
    return jsonify(EnergyAgent(FACILITY_ID).trend())


# ---------------------- Milestone 2: Maintenance Agent ------------------------

@app.route("/api/maintenance/kpis")
def maintenance_kpis():
    return jsonify(MaintenanceAgent(FACILITY_ID).compute_kpis())


@app.route("/api/maintenance/predictions")
def maintenance_predictions():
    return jsonify(MaintenanceAgent(FACILITY_ID).predict_maintenance())


@app.route("/api/maintenance/anomalies")
def maintenance_anomalies():
    return jsonify(MaintenanceAgent(FACILITY_ID).detect_abnormal_behavior())


@app.route("/api/maintenance/lifecycle")
def maintenance_lifecycle():
    return jsonify(MaintenanceAgent(FACILITY_ID).track_asset_lifecycle())


@app.route("/api/maintenance/workorders")
def maintenance_workorders():
    from data.database import get_connection
    conn = get_connection()
    rows = conn.execute(
        """SELECT mr.*, a.asset_name, a.asset_type FROM maintenance_records mr
           JOIN assets a ON mr.asset_id = a.asset_id
           ORDER BY mr.maintenance_date DESC"""
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    simulator.seed()
    threading.Thread(target=background_loop, daemon=True).start()
    print("Agentic FacilityOps AI Platform running -> http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
