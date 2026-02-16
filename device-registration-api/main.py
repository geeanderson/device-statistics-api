  # device-registration-api/main.py
  # Internal API responsible for saving device registrations to the database.
  # Not exposed to external traffic — only the Statistics API calls this service.

  from fastapi import FastAPI
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
  # Endpoints
  # ---------------------------------------------------------------------------

  @app.get("/health")
  def health_check():
      """
      Simple health check. Kubernetes uses this to know if the pod is alive.
      """
      return {"status": "ok", "service": "device-registration-api"}
