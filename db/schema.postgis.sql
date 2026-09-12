-- MotoJá Fortaleza — schema de produção (PostgreSQL + PostGIS)
-- Requer PostgreSQL 13+ e PostGIS instalado no servidor.
-- A aplicação local atual continua usando SQLite; este arquivo é a base da
-- migração para PostgreSQL/PostGIS e não deve ser executado no SQLite.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(100) NOT NULL CHECK (char_length(trim(full_name)) >= 2),
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    user_type VARCHAR(10) NOT NULL CHECK (user_type IN ('PASSENGER', 'DRIVER')),
    rating NUMERIC(3,2) NOT NULL DEFAULT 5.00 CHECK (rating BETWEEN 0.00 AND 5.00),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS driver_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    cnh_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_plate VARCHAR(10) UNIQUE NOT NULL,
    vehicle_model VARCHAR(50) NOT NULL,
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    current_location geometry(Point, 4326),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    passenger_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    driver_id UUID REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'SEARCHING'
        CHECK (status IN ('SEARCHING', 'ACCEPTED', 'ARRIVED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
    origin_location geometry(Point, 4326) NOT NULL,
    destination_location geometry(Point, 4326) NOT NULL,
    origin_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    fare_amount NUMERIC(10,2) NOT NULL CHECK (fare_amount >= 0),
    platform_fee NUMERIC(10,2) NOT NULL CHECK (platform_fee >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,
    CONSTRAINT rides_different_users CHECK (driver_id IS NULL OR passenger_id <> driver_id),
    CONSTRAINT rides_completed_at_check CHECK (
        (status = 'COMPLETED' AND completed_at IS NOT NULL)
        OR (status <> 'COMPLETED')
    )
);

-- Índice GiST para localizar rapidamente motoristas próximos.
CREATE INDEX IF NOT EXISTS idx_driver_profiles_location
    ON driver_profiles USING GIST (current_location);

CREATE INDEX IF NOT EXISTS idx_driver_profiles_online_location
    ON driver_profiles (is_online)
    WHERE is_online = TRUE;

CREATE INDEX IF NOT EXISTS idx_rides_status_created_at
    ON rides (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rides_passenger_created_at
    ON rides (passenger_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_rides_driver_created_at
    ON rides (driver_id, created_at DESC);

-- Mantém updated_at atualizado quando o perfil ou a localização mudar.
CREATE OR REPLACE FUNCTION set_driver_profile_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_driver_profile_updated_at ON driver_profiles;
CREATE TRIGGER trg_driver_profile_updated_at
BEFORE UPDATE ON driver_profiles
FOR EACH ROW
EXECUTE FUNCTION set_driver_profile_updated_at();

-- Valida o SRID e limita coordenadas ao intervalo WGS84 válido.
ALTER TABLE driver_profiles
    DROP CONSTRAINT IF EXISTS driver_profiles_location_valid;
ALTER TABLE driver_profiles
    ADD CONSTRAINT driver_profiles_location_valid CHECK (
        current_location IS NULL
        OR (
            ST_SRID(current_location) = 4326
            AND ST_X(current_location) BETWEEN -180 AND 180
            AND ST_Y(current_location) BETWEEN -90 AND 90
        )
    );

ALTER TABLE rides
    DROP CONSTRAINT IF EXISTS rides_locations_valid;
ALTER TABLE rides
    ADD CONSTRAINT rides_locations_valid CHECK (
        ST_SRID(origin_location) = 4326
        AND ST_SRID(destination_location) = 4326
        AND ST_X(origin_location) BETWEEN -180 AND 180
        AND ST_X(destination_location) BETWEEN -180 AND 180
        AND ST_Y(origin_location) BETWEEN -90 AND 90
        AND ST_Y(destination_location) BETWEEN -90 AND 90
    );

COMMENT ON COLUMN driver_profiles.current_location IS
    'Ponto WGS84: longitude no eixo X e latitude no eixo Y.';
COMMENT ON INDEX idx_driver_profiles_location IS
    'Busca espacial GiST de motoristas próximos.';
