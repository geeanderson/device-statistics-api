  # device-registration-api/main.py
  # Internal API responsible for saving device registrations to the database.
  # Not exposed to external traffic — only the Statistics API calls this service.

  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel
  import os

  # ---------------------------------------------------------------------------
  # App initialization
  # ---------------------------------------------------------------------------

  app = FastAPI(
      title="Device Registration API",
      description="Internal API for registering devices in the database",
      version="1.0.0"
  )

  # ---------------------------------------------------------------------------
  # Configuration — all values come from environment variables, never hardcoded
  # ---------------------------------------------------------------------------

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
  # Request model
  # ---------------------------------------------------------------------------

  class RegisterRequest(BaseModel):
      """Body expected by POST /Device/register"""
      userKey: str
      deviceType: str

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
          200 — registration successful
          400 — invalid device type or missing fields
          500 — database error
      """
      # Reject unknown device types
      if request.deviceType not in VALID_DEVICE_TYPES:
          raise HTTPException(
              status_code=400,
              detail=f"Invalid deviceType '{request.deviceType}'. "
                     f"Allowed values: {sorted(VALID_DEVICE_TYPES)}"
          )

      # Reject empty userKey — it's a required business field
      if not request.userKey or not request.userKey.strip():
          raise HTTPException(status_code=400, detail="userKey cannot be empty")

      return {"statusCode": 200}