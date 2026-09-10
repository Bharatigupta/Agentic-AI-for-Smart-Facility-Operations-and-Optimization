"""
Database layer for the Agentic FacilityOps AI Platform.
Implements the tables needed for Milestone 1 (Energy) and Milestone 2 (Maintenance),
following the schema in Section 9 of the project document (facilities, assets,
energy_usage, maintenance_records, alerts) plus a supporting asset_readings table
that stores the raw IoT sensor stream the Maintenance Agent analyzes.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "facilityops.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS facilities (
            facility_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_name   TEXT NOT NULL,
            facility_type   TEXT,
            location        TEXT
        );

        CREATE TABLE IF NOT EXISTS assets (
            asset_id        INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER,
            asset_name      TEXT,
            asset_type      TEXT,
            status          TEXT DEFAULT 'active',
            install_date    TEXT,
            runtime_hours   REAL DEFAULT 0,
            FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
        );

        CREATE TABLE IF NOT EXISTS energy_usage (
            energy_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER,
            timestamp       TEXT,
            electricity_kwh REAL,
            water_l         REAL,
            hvac_pct        REAL,
            lighting_pct    REAL,
            equipment_pct   REAL,
            other_pct       REAL,
            cost            REAL,
            FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
        );

        CREATE TABLE IF NOT EXISTS asset_readings (
            reading_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id        INTEGER,
            timestamp       TEXT,
            temperature     REAL,
            vibration       REAL,
            health_score    REAL,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
        );

        CREATE TABLE IF NOT EXISTS maintenance_records (
            maintenance_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id                INTEGER,
            issue_type              TEXT,
            maintenance_date        TEXT,
            status                  TEXT,
            priority                TEXT,
            predicted_failure_days  INTEGER,
            FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id  INTEGER,
            alert_type   TEXT,
            severity     TEXT,
            message      TEXT,
            created_at   TEXT
        );
        """
    )
    conn.commit()
    conn.close()
