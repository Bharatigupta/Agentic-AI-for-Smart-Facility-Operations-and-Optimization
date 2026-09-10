"""
MILESTONE 2 - Predictive Maintenance System
Maintenance Agent: monitors equipment health, predicts maintenance needs,
detects abnormal equipment behavior, tracks asset lifecycle, and generates
maintenance work orders automatically for at-risk assets.
"""

import random
import statistics
from datetime import datetime, timedelta

from data.database import get_connection

ASSET_TYPES = [
    "HVAC Unit", "Chiller", "Elevator", "Generator", "Water Pump",
    "Air Handling Unit", "Transformer", "Fire Pump", "Boiler", "Cooling Tower",
]


class MaintenanceAgent:
    def __init__(self, facility_id: int = 1):
        self.facility_id = facility_id

    # ---------------------------------------------------------------
    # 1. Simulate a new IoT sensor cycle for every asset (temp/vibration)
    #    and roll up a health score
    # ---------------------------------------------------------------
    def ingest_readings(self):
        conn = get_connection()
        assets = conn.execute(
            "SELECT * FROM assets WHERE facility_id=?", (self.facility_id,)
        ).fetchall()

        for a in assets:
            # ~10% chance of a "degrading" cycle, otherwise stable operation
            drift = random.uniform(-0.5, 1.6) if random.random() > 0.9 else random.uniform(-0.3, 0.3)
            temperature = 55 + max(drift, 0) * 8 + random.uniform(-2, 2)
            vibration = 2.0 + max(drift, 0) * 1.5 + random.uniform(-0.2, 0.2)
            health_score = max(0, min(100, 100 - max(drift, 0) * 35 - random.uniform(0, 3)))

            conn.execute(
                """INSERT INTO asset_readings (asset_id, timestamp, temperature, vibration, health_score)
                   VALUES (?,?,?,?,?)""",
                (a["asset_id"], datetime.now().isoformat(timespec="seconds"), temperature, vibration, health_score),
            )
            conn.execute(
                "UPDATE assets SET runtime_hours = runtime_hours + ? WHERE asset_id=?",
                (random.uniform(0.8, 1.0), a["asset_id"]),
            )
        conn.commit()
        conn.close()

    def _latest_readings(self):
        conn = get_connection()
        assets = conn.execute(
            "SELECT * FROM assets WHERE facility_id=?", (self.facility_id,)
        ).fetchall()
        result = []
        for a in assets:
            r = conn.execute(
                """SELECT * FROM asset_readings WHERE asset_id=?
                   ORDER BY timestamp DESC LIMIT 1""",
                (a["asset_id"],),
            ).fetchone()
            if r:
                result.append({**dict(a), **dict(r)})
        conn.close()
        return result

    # ---------------------------------------------------------------
    # 2. Monitor equipment health
    # ---------------------------------------------------------------
    def monitor_equipment_health(self):
        return self._latest_readings()

    def health_distribution(self):
        readings = self._latest_readings()
        buckets = {"Excellent": 0, "Good": 0, "Warning": 0, "Critical": 0}
        for r in readings:
            hs = r["health_score"]
            if hs >= 85:
                buckets["Excellent"] += 1
            elif hs >= 65:
                buckets["Good"] += 1
            elif hs >= 40:
                buckets["Warning"] += 1
            else:
                buckets["Critical"] += 1
        total = max(sum(buckets.values()), 1)
        pct = {k: round(v / total * 100, 1) for k, v in buckets.items()}
        return pct, buckets

    # ---------------------------------------------------------------
    # 3. Detect abnormal equipment behavior (z-score anomaly detection)
    # ---------------------------------------------------------------
    def detect_abnormal_behavior(self):
        conn = get_connection()
        anomalies = []
        assets = conn.execute(
            "SELECT * FROM assets WHERE facility_id=?", (self.facility_id,)
        ).fetchall()
        for a in assets:
            rows = conn.execute(
                """SELECT temperature, vibration FROM asset_readings
                   WHERE asset_id=? ORDER BY timestamp DESC LIMIT 12""",
                (a["asset_id"],),
            ).fetchall()
            if len(rows) < 5:
                continue
            temps = [r["temperature"] for r in rows]
            mean_t = statistics.mean(temps)
            sd_t = statistics.pstdev(temps) or 1
            latest = temps[0]
            z = (latest - mean_t) / sd_t
            if abs(z) > 1.8:
                anomalies.append({
                    "asset": a["asset_name"],
                    "asset_type": a["asset_type"],
                    "metric": "temperature",
                    "value": round(latest, 1),
                    "z_score": round(z, 2),
                })
        conn.close()
        return anomalies

    # ---------------------------------------------------------------
    # 4. Predict maintenance requirements
    # ---------------------------------------------------------------
    def predict_maintenance(self):
        readings = self._latest_readings()
        predictions = []
        for r in readings:
            hs = r["health_score"]
            if hs < 40:
                days, risk = random.randint(1, 4), "Critical"
            elif hs < 65:
                days, risk = random.randint(5, 14), "High"
            elif hs < 85:
                days, risk = random.randint(15, 30), "Moderate"
            else:
                days, risk = random.randint(45, 90), "Low"
            predictions.append({
                "asset_id": r["asset_id"],
                "asset_name": r["asset_name"],
                "asset_type": r["asset_type"],
                "health_score": round(hs, 1),
                "risk_level": risk,
                "predicted_days_to_maintenance": days,
            })
        return sorted(predictions, key=lambda x: x["predicted_days_to_maintenance"])

    # ---------------------------------------------------------------
    # 5. Track asset lifecycle
    # ---------------------------------------------------------------
    def track_asset_lifecycle(self, expected_life_days: int = 3650):
        conn = get_connection()
        assets = conn.execute(
            "SELECT * FROM assets WHERE facility_id=?", (self.facility_id,)
        ).fetchall()
        conn.close()
        lifecycle = []
        for a in assets:
            install = datetime.fromisoformat(a["install_date"])
            age_days = (datetime.now() - install).days
            remaining_pct = max(0, round((1 - age_days / expected_life_days) * 100, 1))
            lifecycle.append({
                "asset_name": a["asset_name"],
                "asset_type": a["asset_type"],
                "age_years": round(age_days / 365, 1),
                "runtime_hours": round(a["runtime_hours"], 1),
                "remaining_life_pct": remaining_pct,
            })
        return lifecycle

    # ---------------------------------------------------------------
    # 6. Generate maintenance work orders for Critical/High risk assets
    # ---------------------------------------------------------------
    def generate_work_orders(self):
        conn = get_connection()
        created = []
        for p in self.predict_maintenance():
            if p["risk_level"] in ("Critical", "High"):
                existing = conn.execute(
                    "SELECT * FROM maintenance_records WHERE asset_id=? AND status='Open'",
                    (p["asset_id"],),
                ).fetchone()
                if not existing:
                    conn.execute(
                        """INSERT INTO maintenance_records
                           (asset_id, issue_type, maintenance_date, status, priority, predicted_failure_days)
                           VALUES (?,?,?,?,?,?)""",
                        (
                            p["asset_id"],
                            "Predictive - abnormal wear detected",
                            datetime.now().isoformat(timespec="seconds"),
                            "Open",
                            p["risk_level"],
                            p["predicted_days_to_maintenance"],
                        ),
                    )
                    created.append(p["asset_name"])
        conn.commit()
        conn.close()
        return created

    # ---------------------------------------------------------------
    # 7. KPI roll-up for the Predictive Maintenance Dashboard
    # ---------------------------------------------------------------
    def compute_kpis(self):
        conn = get_connection()
        assets_count = conn.execute(
            "SELECT COUNT(*) c FROM assets WHERE facility_id=?", (self.facility_id,)
        ).fetchone()["c"]
        tickets = conn.execute(
            """SELECT COUNT(*) c FROM maintenance_records mr
               JOIN assets a ON mr.asset_id = a.asset_id
               WHERE a.facility_id=? AND mr.status='Open'""",
            (self.facility_id,),
        ).fetchone()["c"]
        conn.close()

        preds = self.predict_maintenance()
        predicted_failures = len([p for p in preds if p["risk_level"] in ("Critical", "High")])
        dist_pct, _ = self.health_distribution()
        downtime_reduction = round(20 + dist_pct.get("Excellent", 0) * 0.15 + random.uniform(0, 3), 1)

        return {
            "assets_monitored": assets_count,
            "maintenance_tickets": tickets,
            "predicted_failures": predicted_failures,
            "downtime_reduction_pct": downtime_reduction,
            "health_distribution_pct": dist_pct,
        }
