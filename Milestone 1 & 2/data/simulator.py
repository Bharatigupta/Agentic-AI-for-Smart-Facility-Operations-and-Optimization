"""
Seeds the database with a demo facility + assets, backfills 24h of energy
history and several cycles of asset sensor readings, then exposes tick()
to advance the live simulation (called on a timer by app.py).
"""

import random
from datetime import datetime, timedelta

from data.database import get_connection, init_db
from agents.energy_agent import EnergyAgent
from agents.maintenance_agent import MaintenanceAgent, ASSET_TYPES


def seed():
    init_db()
    conn = get_connection()
    existing = conn.execute("SELECT COUNT(*) c FROM facilities").fetchone()["c"]
    if existing:
        conn.close()
        return

    conn.execute(
        "INSERT INTO facilities (facility_name, facility_type, location) VALUES (?,?,?)",
        ("Corporate Tower A", "Office Complex", "Bengaluru, IN"),
    )
    facility_id = conn.execute("SELECT facility_id FROM facilities LIMIT 1").fetchone()["facility_id"]

    for i in range(14):
        install_days_ago = random.randint(200, 3200)
        install_date = (datetime.now() - timedelta(days=install_days_ago)).isoformat(timespec="seconds")
        atype = ASSET_TYPES[i % len(ASSET_TYPES)]
        conn.execute(
            """INSERT INTO assets (facility_id, asset_name, asset_type, status, install_date, runtime_hours)
               VALUES (?,?,?,?,?,?)""",
            (facility_id, f"{atype} #{i + 1}", atype, "active", install_date, random.uniform(500, 20000)),
        )
    conn.commit()
    conn.close()

    # Backfill 24 hourly energy readings so the dashboard has an immediate trend line
    energy = EnergyAgent(facility_id)
    for _ in range(24):
        energy.ingest_reading()

    # Seed several sensor cycles so anomaly detection / health scoring has history
    maintenance = MaintenanceAgent(facility_id)
    for _ in range(12):
        maintenance.ingest_readings()
    maintenance.generate_work_orders()


def tick(facility_id: int = 1):
    """Advance the live simulation by one step. Called periodically by app.py."""
    EnergyAgent(facility_id).ingest_reading()
    m = MaintenanceAgent(facility_id)
    m.ingest_readings()
    m.generate_work_orders()
