"""Populate the IOSA refinery database with simulated but realistic data.

Equipment tags, types, and incident scenarios are modeled on typical
petrochemical/refinery operations. Data is deterministic (no randomness)
so the database is reproducible across runs.
"""
from src.iosa.database.db import init_db, get_connection
from src.iosa.logger import setup_logger

logger = setup_logger(__name__)

EQUIPMENT = [
    ("P-101", "Crude Feed Pump A", "pump", "CDU", "2015-03-12", "active"),
    ("P-102", "Crude Feed Pump B", "pump", "CDU", "2015-03-12", "maintenance"),
    ("P-201", "Reflux Pump", "pump", "CDU", "2016-06-01", "active"),
    ("T-101", "Crude Oil Storage Tank 1", "tank", "Tank Farm", "2010-01-15", "active"),
    ("T-102", "Crude Oil Storage Tank 2", "tank", "Tank Farm", "2010-01-15", "active"),
    ("T-103", "Naphtha Intermediate Tank", "tank", "Tank Farm", "2012-08-20", "active"),
    ("T-104", "Heavy Raffinate Tank", "tank", "Tank Farm", "2011-05-10", "decommissioned"),
    ("V-101", "Crude Column Feed Valve", "valve", "CDU", "2015-03-12", "active"),
    ("V-102", "Reflux Control Valve", "valve", "CDU", "2016-06-01", "active"),
    ("V-103", "Blowdown Valve", "valve", "ISOM", "2014-09-22", "active"),
    ("C-101", "Hydrogen Compressor", "compressor", "ISOM", "2013-11-08", "active"),
    ("C-102", "Recycle Gas Compressor", "compressor", "CCR", "2017-02-14", "active"),
    ("HX-101", "Crude Preheater", "heat_exchanger", "CDU", "2015-03-12", "active"),
    ("HX-102", "Naphtha Cooler", "heat_exchanger", "CDU", "2016-06-01", "active"),
    ("DC-101", "Atmospheric Distillation Column", "distillation_column", "CDU", "2010-01-15", "active"),
    ("DC-102", "Raffinate Splitter Tower", "distillation_column", "ISOM", "2012-08-20", "active"),
    ("R-101", "Catalytic Reformer Reactor", "reactor", "CCR", "2013-11-08", "active"),
    ("R-102", "Hydrotreater Reactor", "reactor", "NHT", "2014-09-22", "active"),
]

INCIDENTS = [
    (1, "2023-06-15 08:30:00", "high", "leak", "Mechanical seal failure on P-101 causing hydrocarbon leak to atmosphere. Area isolated within 12 minutes.", "Seal degradation due to exceeding MTBR interval", 0, 48.0, 1, "2023-06-17 14:00:00", "Operator A. Rahman"),
    (2, "2024-01-22 03:15:00", "critical", "shutdown", "P-102 emergency shutdown triggered by high bearing temperature alarm at 125C. Vibration readings had been trending upward for 2 weeks.", "Bearing failure from inadequate lubrication schedule", 0, 72.0, 1, "2024-01-25 08:00:00", "Shift Lead M. Hassan"),
    (4, "2023-09-10 14:00:00", "medium", "near_miss", "T-101 high level alarm activated at 92% capacity during crude receipt. Inlet valve V-101 closed automatically.", "Operator distraction during simultaneous tank transfers", 0, 2.0, 1, "2023-09-10 16:00:00", "Operator K. Ahmadi"),
    (7, "2024-03-05 11:30:00", "high", "leak", "T-104 bottom nozzle flange leak detected during routine inspection. Tank had been out of service for scheduled maintenance.", "Gasket degradation, tank exceeded inspection interval by 6 months", 0, 120.0, 1, "2024-03-10 09:00:00", "Inspector R. Karimi"),
    (10, "2023-11-18 22:45:00", "medium", "equipment_failure", "V-103 blowdown valve failed to open during emergency depressuring drill. Actuator air supply line found corroded.", "Corrosion of instrument air tubing in outdoor exposure", 0, 8.0, 1, "2023-11-19 06:00:00", "Instrument Tech S. Nazari"),
    (11, "2024-02-14 06:00:00", "high", "shutdown", "C-101 hydrogen compressor tripped on high discharge temperature at 165C. Anti-surge valve cycled repeatedly before trip.", "Fouled intercooler reducing heat rejection capacity", 0, 36.0, 1, "2024-02-15 18:00:00", "Shift Lead M. Hassan"),
    (15, "2023-08-01 10:15:00", "low", "near_miss", "DC-101 tray differential pressure rose to 0.8 bar during heavy crude processing. Operators reduced feed rate by 15% to stabilize.", "Feed composition change not communicated from upstream", 0, 0.0, 1, "2023-08-01 12:00:00", "Board Op F. Torabi"),
    (16, "2024-04-20 09:00:00", "critical", "fire", "DC-102 raffinate splitter overhead line fire caused by flange leak on hot vapor line. Fire suppression activated, area evacuated.", "Flange bolt relaxation from thermal cycling, missed in last turnaround inspection", 1, 168.0, 1, "2024-04-27 08:00:00", "HSE Lead B. Mohammadi"),
    (17, "2023-12-10 16:30:00", "medium", "equipment_failure", "R-101 catalyst bed temperature excursion to 485C, 35C above normal operating limit. Reactor brought to safe shutdown.", "Maldistribution of feed across catalyst bed inlet", 0, 24.0, 1, "2023-12-11 16:00:00", "Process Engineer J. Rezaei"),
]

MAINTENANCE_LOGS = [
    (1, "2023-01-15 08:00:00", "preventive", "Replaced mechanical seal on P-101 per scheduled maintenance plan.", "Tech A. Karimi", 6.0, 4500.0, "Mechanical seal assembly", "2023-07-15"),
    (1, "2023-07-20 08:00:00", "preventive", "Bearing inspection and lubrication on P-101. Vibration baseline recorded.", "Tech A. Karimi", 4.0, 800.0, None, "2024-01-20"),
    (2, "2024-01-25 08:00:00", "corrective", "Emergency bearing replacement on P-102 after high-temp shutdown. Both drive-end and non-drive-end bearings replaced.", "Tech A. Karimi", 16.0, 12000.0, "SKF 6310 bearings x2, lubricant", "2024-07-25"),
    (4, "2023-03-01 08:00:00", "inspection", "API 653 external inspection of T-101. No corrosion above threshold. Shell thickness within spec.", "Inspector R. Karimi", 8.0, 2000.0, None, "2025-03-01"),
    (7, "2024-03-10 08:00:00", "corrective", "T-104 bottom nozzle flange gasket replacement. Tank cleaned and inspected internally before return to service. Decision made to decommission.", "Tech B. Hosseini", 40.0, 8500.0, "Spiral wound gasket, flange bolts", None),
    (10, "2023-11-19 06:00:00", "corrective", "Replaced corroded instrument air tubing on V-103 blowdown valve actuator. Full stroke test passed.", "Instrument Tech S. Nazari", 4.0, 600.0, "SS instrument tubing 3m, fittings", "2024-05-19"),
    (11, "2024-02-16 08:00:00", "corrective", "Cleaned and pressure-tested C-101 intercooler. Restored heat transfer capacity. Discharge temp verified at 142C post-repair.", "Tech D. Rahimi", 12.0, 3200.0, None, "2024-08-16"),
    (11, "2024-08-20 08:00:00", "predictive", "Vibration analysis on C-101 showed normal signature. Oil sample analysis within acceptable limits.", "Tech D. Rahimi", 3.0, 500.0, None, "2025-02-20"),
    (15, "2023-06-15 08:00:00", "inspection", "DC-101 tray inspection during planned turnaround. 3 trays showed minor corrosion, within allowable limits.", "Inspector R. Karimi", 24.0, 5000.0, None, "2025-06-15"),
    (17, "2023-12-12 08:00:00", "corrective", "R-101 catalyst bed leveling and inlet distributor inspection. Feed maldistribution corrected.", "Process Tech E. Ghasemi", 18.0, 15000.0, "Catalyst support balls 200kg", "2024-06-12"),
]

PUMP_READINGS = [
    (1, 2.1, 8.5, 6.4, 120.0, 85.0, 55.0, 2980, 62.0, 78.0, 2.1, 0, 75.0, "2024-06-01 06:00:00"),
    (1, 2.0, 8.4, 6.4, 118.0, 84.0, 54.0, 2975, 63.0, 79.0, 2.2, 0, 73.0, "2024-06-01 12:00:00"),
    (1, 2.1, 8.6, 6.5, 122.0, 86.0, 56.0, 2982, 64.0, 80.0, 2.5, 0, 76.0, "2024-06-01 18:00:00"),
    (2, 2.0, 8.3, 6.3, 115.0, 88.0, 57.0, 2960, 95.0, 82.0, 4.8, 0, 70.0, "2024-01-21 06:00:00"),
    (2, 2.0, 8.2, 6.2, 112.0, 90.0, 59.0, 2955, 110.0, 88.0, 6.2, 0, 68.0, "2024-01-21 18:00:00"),
    (2, 1.9, 8.0, 6.1, 108.0, 95.0, 62.0, 2940, 125.0, 95.0, 8.5, 0, 65.0, "2024-01-22 03:00:00"),
]

TANK_READINGS = [
    (4, 75.0, 12000.0, 32.0, 1.01, 50.0, 45.0, "2024-06-01 06:00:00"),
    (4, 78.0, 12480.0, 33.0, 1.01, 55.0, 40.0, "2024-06-01 12:00:00"),
    (4, 92.0, 14720.0, 34.0, 1.02, 60.0, 30.0, "2023-09-10 13:45:00"),
    (5, 60.0, 9600.0, 30.0, 1.01, 40.0, 40.0, "2024-06-01 06:00:00"),
    (7, 45.0, 5400.0, 28.0, 1.00, 0.0, 0.0, "2024-02-15 08:00:00"),
]


def seed():
    init_db()
    conn = get_connection()

    row_count = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
    if row_count > 0:
        logger.info("seed: database already populated, skipping")
        conn.close()
        return

    conn.executemany(
        "INSERT INTO equipment (tag, name, type, unit, install_date, status) VALUES (?, ?, ?, ?, ?, ?)",
        EQUIPMENT,
    )

    conn.executemany(
        "INSERT INTO incidents (equipment_id, incident_date, severity, incident_type, description, root_cause, injuries_count, downtime_hours, resolved, resolved_date, reported_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        INCIDENTS,
    )

    conn.executemany(
        "INSERT INTO maintenance_logs (equipment_id, maintenance_date, maintenance_type, description, technician, duration_hours, cost, parts_replaced, next_scheduled_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        MAINTENANCE_LOGS,
    )

    conn.executemany(
        "INSERT INTO pump_readings (equipment_id, suction_pressure_bar, discharge_pressure_bar, differential_pressure_bar, flow_rate_m3_per_h, motor_current_amps, motor_power_kw, speed_rpm, bearing_temperature_c, motor_temperature_c, vibration_mm_s, seal_leakage, suction_level_percent, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        PUMP_READINGS,
    )

    conn.executemany(
        "INSERT INTO tank_readings (equipment_id, level_percent, volume_m3, temperature_c, pressure_bar, inlet_flow_rate_m3_per_h, outlet_flow_rate_m3_per_h, recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        TANK_READINGS,
    )

    conn.commit()
    conn.close()

    logger.info(
        f"seed: inserted {len(EQUIPMENT)} equipment, {len(INCIDENTS)} incidents, "
        f"{len(MAINTENANCE_LOGS)} maintenance logs, {len(PUMP_READINGS)} pump readings, "
        f"{len(TANK_READINGS)} tank readings"
    )


if __name__ == "__main__":
    seed()
