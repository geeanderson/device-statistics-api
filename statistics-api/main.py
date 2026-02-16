  # Public-facing API that receives login events and returns device statistics.
  # This service is the entry point for external traffic.
  # It calls the Device Registration API internally to persist data.

  from fastapi import FastAPI
  import os

  app = FastAPI(
      title="Statistics API",
      description="Public API for logging authentication events and retrieving device statistics",
      version="1.0.0"
  )

  DEVICE_API_URL = os.getenv("DEVICE_API_URL", "http://localhost:8001")

  DB_HOST     = os.getenv("DB_HOST", "localhost")
  DB_PORT     = os.getenv("DB_PORT", "5432")
  DB_NAME     = os.getenv("DB_NAME", "devicedb")
  DB_USER     = os.getenv("DB_USER", "postgres")
  DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

  VALID_DEVICE_TYPES = {"iOS", "Android", "Watch", "TV"}

  @app.get("/health")
  def health_check():
      """
      Simple health check. Kubernetes uses this to know if the pod is alive.
      """
      return {"status": "ok", "service": "statistics-api"}