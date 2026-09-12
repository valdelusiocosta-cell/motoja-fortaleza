-- MotoJá Fortaleza — schema PostgreSQL + PostGIS compatível com a API do MVP.
-- Use este schema para DATABASE_URL; schema.postgis.sql é a versão mínima
-- baseada no modelo espacial fornecido inicialmente.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) GENERATED ALWAYS AS (name) STORED,
    phone VARCHAR(30) UNIQUE NOT NULL,
    email VARCHAR(160) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('passenger', 'driver', 'admin')),
    status VARCHAR(12) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS driver_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    approval_status VARCHAR(12) NOT NULL DEFAULT 'pending'
        CHECK (approval_status IN ('pending', 'approved', 'suspended')),
    online BOOLEAN NOT NULL DEFAULT FALSE,
    cpf VARCHAR(20),
    cnh VARCHAR(30),
    cnh_number VARCHAR(30),
    ear BOOLEAN NOT NULL DEFAULT FALSE,
    vehicle_model VARCHAR(80) DEFAULT 'Honda CG 160',
    vehicle_plate VARCHAR(10) DEFAULT 'A CONFIRMAR',
    vehicle_year INTEGER,
    rating NUMERIC(3,2) NOT NULL DEFAULT 5.00 CHECK (rating BETWEEN 0 AND 5),
    current_location geometry(Point, 4326),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    driver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind VARCHAR(60) NOT NULL,
    filename VARCHAR(120) NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ,
    review_note TEXT
);

CREATE TABLE IF NOT EXISTS fare_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    base DOUBLE PRECISION NOT NULL CHECK (base >= 0),
    per_km DOUBLE PRECISION NOT NULL CHECK (per_km >= 0),
    per_min DOUBLE PRECISION NOT NULL CHECK (per_min >= 0),
    minimum DOUBLE PRECISION NOT NULL CHECK (minimum >= 0),
    commission DOUBLE PRECISION NOT NULL CHECK (commission >= 0 AND commission < 1),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rides (
    id TEXT PRIMARY KEY,
    passenger_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    driver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    origin_lat DOUBLE PRECISION,
    origin_lng DOUBLE PRECISION,
    destination_lat DOUBLE PRECISION,
    destination_lng DOUBLE PRECISION,
    origin_location geometry(Point, 4326),
    destination_location geometry(Point, 4326),
    payment_method VARCHAR(20) NOT NULL,
    distance_km DOUBLE PRECISION NOT NULL CHECK (distance_km >= 0),
    duration_min INTEGER NOT NULL CHECK (duration_min >= 0),
    fare DOUBLE PRECISION NOT NULL CHECK (fare >= 0),
    fare_amount DOUBLE PRECISION GENERATED ALWAYS AS (fare) STORED,
    platform_fee DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (platform_fee >= 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('searching', 'accepted', 'in_progress', 'finished', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancel_reason TEXT,
    CONSTRAINT rides_different_users CHECK (driver_id IS NULL OR driver_id <> passenger_id)
);

CREATE TABLE IF NOT EXISTS ride_events (
    id BIGSERIAL PRIMARY KEY,
    ride_id TEXT NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event VARCHAR(40) NOT NULL,
    detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
    id BIGSERIAL PRIMARY KEY,
    ride_id TEXT UNIQUE NOT NULL REFERENCES rides(id) ON DELETE CASCADE,
    passenger_id UUID NOT NULL REFERENCES users(id),
    driver_id UUID REFERENCES users(id),
    score INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incidents (
    id BIGSERIAL PRIMARY KEY,
    ride_id TEXT REFERENCES rides(id) ON DELETE SET NULL,
    reporter_id UUID NOT NULL REFERENCES users(id),
    type VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_driver_profiles_location
    ON driver_profiles USING GIST (current_location);
CREATE INDEX IF NOT EXISTS idx_driver_profiles_online_location
    ON driver_profiles (online) WHERE online = TRUE;
CREATE INDEX IF NOT EXISTS idx_rides_status_created_at
    ON rides (status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rides_passenger_created_at
    ON rides (passenger_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rides_driver_created_at
    ON rides (driver_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ride_events_ride_created_at
    ON ride_events (ride_id, created_at);
CREATE INDEX IF NOT EXISTS idx_incidents_status_created_at
    ON incidents (status, created_at DESC);

CREATE OR REPLACE FUNCTION set_driver_profile_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_driver_profile_updated_at ON driver_profiles;
CREATE TRIGGER trg_driver_profile_updated_at
BEFORE UPDATE ON driver_profiles
FOR EACH ROW EXECUTE FUNCTION set_driver_profile_updated_at();

INSERT INTO fare_config(id, base, per_km, per_min, minimum, commission)
VALUES (1, 3.50, 1.35, 0.18, 7.50, 0.20)
ON CONFLICT (id) DO NOTHING;
