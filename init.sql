-- init.sql
-- PostgreSQL initialization script.
-- This file is executed automatically when the PostgreSQL container starts for the first time.

CREATE TABLE IF NOT EXISTS device_registrations (
    id          SERIAL          PRIMARY KEY,
    user_key    VARCHAR(255)    NOT NULL,
    device_type VARCHAR(50)     NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);


-- Index: speed up COUNT queries filtered by device_type
-- The GET /Log/auth/statistics endpoint filters by device_type on every request,

CREATE INDEX IF NOT EXISTS idx_device_registrations_device_type
    ON device_registrations (device_type);
