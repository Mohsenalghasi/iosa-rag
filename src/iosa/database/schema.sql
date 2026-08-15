-- IOSA-RAG Module 5: Refinery Database Schema
-- SQLite schema for simulated refinery equipment, incidents, and maintenance data.
-- See refinery_equipment_schema_reference.md for column-by-column design rationale.

PRAGMA foreign_keys = ON;

-- ============================================================
-- Core equipment table
-- ============================================================
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('pump','tank','valve','compressor','heat_exchanger','distillation_column','reactor')),
    unit TEXT NOT NULL,
    install_date DATE,
    status TEXT NOT NULL CHECK(status IN ('active','maintenance','decommissioned'))
);

-- ============================================================
-- Incidents (shared across all equipment types)
-- ============================================================
CREATE TABLE incidents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    incident_date DATETIME NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('low','medium','high','critical')),
    incident_type TEXT NOT NULL CHECK(incident_type IN ('leak','fire','explosion','shutdown','near_miss','spill','equipment_failure')),
    description TEXT NOT NULL,
    root_cause TEXT,
    injuries_count INTEGER NOT NULL DEFAULT 0,
    downtime_hours REAL,
    resolved INTEGER NOT NULL CHECK(resolved IN (0,1)),
    resolved_date DATETIME,
    reported_by TEXT
);

CREATE INDEX idx_incidents_equipment ON incidents(equipment_id);
CREATE INDEX idx_incidents_date ON incidents(incident_date);

-- ============================================================
-- Maintenance logs (shared across all equipment types)
-- ============================================================
CREATE TABLE maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    maintenance_date DATETIME NOT NULL,
    maintenance_type TEXT NOT NULL CHECK(maintenance_type IN ('preventive','corrective','predictive','inspection')),
    description TEXT NOT NULL,
    technician TEXT NOT NULL,
    duration_hours REAL,
    cost REAL,
    parts_replaced TEXT,
    next_scheduled_date DATE
);

CREATE INDEX idx_maintenance_equipment ON maintenance_logs(equipment_id);
CREATE INDEX idx_maintenance_date ON maintenance_logs(maintenance_date);

-- ============================================================
-- Pump readings
-- ============================================================
CREATE TABLE pump_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    suction_pressure_bar REAL,
    discharge_pressure_bar REAL,
    differential_pressure_bar REAL,
    flow_rate_m3_per_h REAL,
    motor_current_amps REAL,
    motor_power_kw REAL,
    speed_rpm REAL,
    bearing_temperature_c REAL,
    motor_temperature_c REAL,
    vibration_mm_s REAL,
    seal_leakage INTEGER CHECK(seal_leakage IN (0,1)),
    suction_level_percent REAL CHECK(suction_level_percent >= 0 AND suction_level_percent <= 100),
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_pump_readings_equipment_time ON pump_readings(equipment_id, recorded_at);

-- ============================================================
-- Tank readings
-- ============================================================
CREATE TABLE tank_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    level_percent REAL CHECK(level_percent >= 0 AND level_percent <= 100),
    volume_m3 REAL,
    temperature_c REAL,
    pressure_bar REAL,
    inlet_flow_rate_m3_per_h REAL,
    outlet_flow_rate_m3_per_h REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_tank_readings_equipment_time ON tank_readings(equipment_id, recorded_at);

-- ============================================================
-- Valve readings
-- ============================================================
CREATE TABLE valve_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    position_percent REAL CHECK(position_percent >= 0 AND position_percent <= 100),
    commanded_position_percent REAL CHECK(commanded_position_percent >= 0 AND commanded_position_percent <= 100),
    upstream_pressure_bar REAL,
    downstream_pressure_bar REAL,
    differential_pressure_bar REAL,
    flow_rate_m3_per_h REAL,
    actuator_air_pressure_bar REAL,
    travel_time_s REAL,
    temperature_c REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_valve_readings_equipment_time ON valve_readings(equipment_id, recorded_at);

-- ============================================================
-- Compressor readings
-- ============================================================
CREATE TABLE compressor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    suction_pressure_bar REAL,
    discharge_pressure_bar REAL,
    suction_temperature_c REAL,
    discharge_temperature_c REAL,
    flow_rate_m3_per_h REAL,
    vibration_mm_s REAL,
    bearing_temperature_c REAL,
    motor_current_amps REAL,
    speed_rpm REAL,
    oil_pressure_bar REAL,
    oil_temperature_c REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_compressor_readings_equipment_time ON compressor_readings(equipment_id, recorded_at);

-- ============================================================
-- Heat exchanger readings
-- ============================================================
CREATE TABLE heat_exchanger_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    hot_side_inlet_temp_c REAL,
    hot_side_outlet_temp_c REAL,
    cold_side_inlet_temp_c REAL,
    cold_side_outlet_temp_c REAL,
    hot_side_flow_rate_m3_per_h REAL,
    cold_side_flow_rate_m3_per_h REAL,
    pressure_drop_bar REAL,
    fouling_factor REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_heat_exchanger_readings_equipment_time ON heat_exchanger_readings(equipment_id, recorded_at);

-- ============================================================
-- Distillation column readings
-- ============================================================
CREATE TABLE distillation_column_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    feed_rate_m3_per_h REAL,
    overhead_temperature_c REAL,
    bottom_temperature_c REAL,
    overhead_pressure_bar REAL,
    reflux_ratio REAL,
    reboiler_duty_kw REAL,
    tray_differential_pressure_bar REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_distillation_column_readings_equipment_time ON distillation_column_readings(equipment_id, recorded_at);

-- ============================================================
-- Reactor readings
-- ============================================================
CREATE TABLE reactor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    reactor_temperature_c REAL,
    reactor_pressure_bar REAL,
    feed_rate_m3_per_h REAL,
    catalyst_bed_temperature_c REAL,
    conversion_rate_percent REAL CHECK(conversion_rate_percent >= 0 AND conversion_rate_percent <= 100),
    coolant_flow_rate_m3_per_h REAL,
    recorded_at DATETIME NOT NULL
);

CREATE INDEX idx_reactor_readings_equipment_time ON reactor_readings(equipment_id, recorded_at);