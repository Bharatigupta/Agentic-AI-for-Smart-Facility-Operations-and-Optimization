"""
MILESTONE 1 - Energy Intelligence & Monitoring
Energy Agent: monitors electricity/water/utility consumption, detects wastage,
analyzes HVAC efficiency, optimizes lighting schedules, generates savings
recommendations, and forecasts future demand.
"""

import random
import statistics
from datetime import datetime

from data.database import get_connection


class EnergyAgent:
    def __init__(self, facility_id: int = 1):
        self.facility_id = facility_id

    # ---------------------------------------------------------------
    # 1. Integrate utility & IoT data (simulated ingestion of a reading)
    # ---------------------------------------------------------------
    def ingest_reading(self):
        conn = get_connection()
        hour = datetime.now().hour
        occupancy_factor = 1.0 if 8 <= hour <= 19 else 0.4

        base = random.uniform(35, 55) * occupancy_factor
        hvac = base * random.uniform(0.40, 0.50)
        lighting = base * random.uniform(0.22, 0.32)
        equipment = base * random.uniform(0.15, 0.22)
        other = max(base - hvac - lighting - equipment, 1)
        total = hvac + lighting + equipment + other
        water = random.uniform(200, 600) * occupancy_factor
        cost = total * 0.12  # $ per kWh tariff

        conn.execute(
            """INSERT INTO energy_usage
               (facility_id, timestamp, electricity_kwh, water_l,
                hvac_pct, lighting_pct, equipment_pct, other_pct, cost)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                self.facility_id,
                datetime.now().isoformat(timespec="seconds"),
                total,
                water,
                hvac / total * 100,
                lighting / total * 100,
                equipment / total * 100,
                other / total * 100,
                cost,
            ),
        )
        conn.commit()
        conn.close()

    def get_recent(self, limit: int = 24):
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM energy_usage WHERE facility_id=?
               ORDER BY timestamp DESC LIMIT ?""",
            (self.facility_id, limit),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ---------------------------------------------------------------
    # 2. Energy consumption analytics -> KPI cards for the dashboard
    # ---------------------------------------------------------------
    def compute_kpis(self):
        rows = self.get_recent(24)
        if not rows:
            return {
                "total_energy_mwh": 0, "cost_savings": 0,
                "efficiency_score": 0, "carbon_reduction_pct": 0,
                "distribution": {},
            }

        total_kwh = sum(r["electricity_kwh"] for r in rows)
        baseline = total_kwh * 1.18  # assumed pre-optimization baseline
        savings = max(baseline - total_kwh, 0) * 0.12
        efficiency_score = self._efficiency_score(rows)
        carbon_reduction = round(
            min(30, (savings / (baseline * 0.12 + 0.01)) * 100 + random.uniform(2, 5)), 1
        )

        return {
            "total_energy_mwh": round(total_kwh / 1000, 2),
            "cost_savings": round(savings, 2),
            "efficiency_score": efficiency_score,
            "carbon_reduction_pct": carbon_reduction,
            "distribution": self._distribution(rows),
        }

    def _distribution(self, rows):
        return {
            "HVAC Systems": round(statistics.mean(r["hvac_pct"] for r in rows), 1),
            "Lighting": round(statistics.mean(r["lighting_pct"] for r in rows), 1),
            "Equipment": round(statistics.mean(r["equipment_pct"] for r in rows), 1),
            "Other Systems": round(statistics.mean(r["other_pct"] for r in rows), 1),
        }

    def _efficiency_score(self, rows):
        usages = [r["electricity_kwh"] for r in rows]
        if len(usages) < 2:
            return 80
        mean = statistics.mean(usages)
        cv = (statistics.pstdev(usages) / mean) if mean else 0
        return round(max(50, min(98, 95 - cv * 40)))

    # ---------------------------------------------------------------
    # 3. Detect energy wastage patterns
    # ---------------------------------------------------------------
    def detect_wastage(self):
        events = []
        for r in self.get_recent(24):
            ts = datetime.fromisoformat(r["timestamp"])
            if (ts.hour < 7 or ts.hour > 21) and r["electricity_kwh"] > 25:
                events.append({
                    "timestamp": r["timestamp"],
                    "usage_kwh": round(r["electricity_kwh"], 1),
                    "issue": "High off-hours consumption detected",
                })
        return events

    # ---------------------------------------------------------------
    # 4. Analyze HVAC efficiency
    # ---------------------------------------------------------------
    def analyze_hvac_efficiency(self):
        rows = self.get_recent(24)
        if not rows:
            return {"avg_hvac_load_pct": 0, "status": "No data yet"}
        avg = statistics.mean(r["hvac_pct"] for r in rows)
        if avg > 48:
            status = "Underperforming - check filters & setpoints"
        elif avg > 42:
            status = "Moderate - monitor closely"
        else:
            status = "Optimal"
        return {"avg_hvac_load_pct": round(avg, 1), "status": status}

    # ---------------------------------------------------------------
    # 5. Optimize lighting schedules
    # ---------------------------------------------------------------
    def optimize_lighting_schedule(self):
        hour = datetime.now().hour
        recs = []
        if hour >= 19 or hour <= 6:
            recs.append("Dim non-essential lighting zones to 20% during off-hours.")
        recs.append("Auto-shutoff lighting in unoccupied zones after 30 minutes idle.")
        recs.append("Align lighting schedule with daylight sensors at sunrise/sunset.")
        return recs

    # ---------------------------------------------------------------
    # 6. Generate energy-saving recommendations
    # ---------------------------------------------------------------
    def generate_recommendations(self):
        recs = []
        wastage = self.detect_wastage()
        hvac = self.analyze_hvac_efficiency()

        if wastage:
            recs.append(f"{len(wastage)} off-hours wastage event(s) detected - enforce automatic shutdown policy.")
        if hvac["status"].startswith("Underperforming"):
            recs.append("HVAC load elevated - schedule filter replacement and recalibrate thermostats.")
        recs.extend(self.optimize_lighting_schedule())
        recs.append("Shift non-critical equipment loads to off-peak tariff hours to cut cost.")
        return recs

    # ---------------------------------------------------------------
    # 7. Forecast future energy demand
    # ---------------------------------------------------------------
    def forecast_demand(self, hours_ahead: int = 6):
        rows = list(reversed(self.get_recent(24)))
        if len(rows) < 3:
            return []
        usages = [r["electricity_kwh"] for r in rows]
        trend = (usages[-1] - usages[0]) / len(usages)
        last = usages[-1]
        forecast = []
        for h in range(1, hours_ahead + 1):
            hour = (datetime.now().hour + h) % 24
            occupancy_factor = 1.0 if 8 <= hour <= 19 else 0.5
            projected = max(5, (last + trend * h) * occupancy_factor)
            forecast.append({"hour": f"{hour:02d}:00", "projected_kwh": round(projected, 1)})
        return forecast

    def trend(self, limit: int = 24):
        rows = list(reversed(self.get_recent(limit)))
        return [{"time": r["timestamp"][11:16], "kwh": round(r["electricity_kwh"], 1)} for r in rows]
