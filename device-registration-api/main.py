# Internal API responsible for saving device registrations to the database.
# Not exposed to external traffic — only the Statistics API calls this service.

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import psycopg2
import os

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
# Create the FastAPI app with metadata shown in the auto-generated /docs page
app = FastAPI(
    title="Device Registration API",
    description="Internal API for registering devices in the database",
    version="1.0.0"
)

# ---------------------------------------------------------------------------
# Configuration — all values come from environment variables, never hardcoded
# ---------------------------------------------------------------------------
# PostgreSQL connection parameters — injected via docker-compose or K8s Secret
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME", "devicedb")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# ---------------------------------------------------------------------------
# Valid device types — used for input validation
# ---------------------------------------------------------------------------

VALID_DEVICE_TYPES = {"iOS", "Android", "Watch", "TV"}

# ---------------------------------------------------------------------------
# Request model (Pydantic validates incoming JSON automatically)
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Body expected by POST /Device/register"""
    userKey: str
    deviceType: str

# ---------------------------------------------------------------------------
# Helper: database connection
# ---------------------------------------------------------------------------

def get_db_connection():
    """
    Opens a new database connection using the env vars.
    We open one per request and close it in the finally block
    to avoid holding idle connections.
    """
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Simple health check. Kubernetes uses this to know if the pod is alive.
    """
    return {"status": "ok", "service": "device-registration-api"}


@app.post("/Device/register")
def register_device(request: RegisterRequest):
    """
    Saves a device registration to the database.
    This is an internal endpoint — only the Statistics API should call it,
    never external clients.

    Returns:
        200 — {"statusCode": 200} registration successful
        400 — {"statusCode": 400} invalid device type, missing fields, or database error
    """
    # Reject unknown device types
    if request.deviceType not in VALID_DEVICE_TYPES:
        return JSONResponse(
            status_code=400,
            content={"statusCode": 400}
        )

    # Reject empty userKey — it's a required business field
    if not request.userKey or not request.userKey.strip():
        return JSONResponse(
            status_code=400,
            content={"statusCode": 400}
        )

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Parameterized INSERT — %s placeholders prevent SQL injection
        # created_at is handled by the DEFAULT in the table schema (see init.sql)
        cursor.execute(
            "INSERT INTO device_registrations (user_key, device_type) VALUES (%s, %s)",
            (request.userKey.strip(), request.deviceType)
        )

        conn.commit()

        return {"statusCode": 200}

    except Exception as e:
        if conn:
            conn.rollback()
        return JSONResponse(
            status_code=400,
            content={"statusCode": 400}
        )

    finally:
        if conn:
            conn.close()