-- init.sql
-- PostgreSQL initialization script.

CREATE TABLE IF NOT EXISTS device_registrations (
    id          SERIAL          PRIMARY KEY,
    user_key    VARCHAR(255)    NOT NULL,
    device_type VARCHAR(50)     NOT NULL,
    created_at  TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_device_registrations_device_type
    ON device_registrations (device_type);
