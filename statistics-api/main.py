  # Public-facing API that receives login events and returns device statistics.
  # This service is the entry point for external traffic.
  # It calls the Device Registration API internally to persist data.

  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel
  import httpx
  import os

  # ---------------------------------------------------------------------------
  # App initialization
  # ---------------------------------------------------------------------------

  app = FastAPI(
      title="Statistics API",
      description="Public API for logging authentication events and retrieving device 
  statistics",
      version="1.0.0"
  )

  # ---------------------------------------------------------------------------
  # Configuration — all values come from environment variables, never hardcoded
  # ---------------------------------------------------------------------------

  DEVICE_API_URL = os.getenv("DEVICE_API_URL", "http://localhost:8001")

  DB_HOST     = os.getenv("DB_HOST", "localhost")
  DB_PORT     = os.getenv("DB_PORT", "5432")
  DB_NAME     = os.getenv("DB_NAME", "devicedb")
  DB_USER     = os.getenv("DB_USER", "postgres")
  DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

  # ---------------------------------------------------------------------------
  # Valid device types — used for input validation on every endpoint
  # ---------------------------------------------------------------------------

  VALID_DEVICE_TYPES = {"iOS", "Android", "Watch", "TV"}

  # ---------------------------------------------------------------------------
  # Request model
  # ---------------------------------------------------------------------------

  class AuthLogRequest(BaseModel):
      """Body expected by POST /Log/auth"""
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
      return {"status": "ok", "service": "statistics-api"}


  @app.post("/Log/auth")
  async def log_auth(request: AuthLogRequest):
      """
      Main endpoint. Receives a login event, checks if the device type is valid,
      then calls the Device Registration API to save the record.

      Returns:
          200 — registration successful
          400 — invalid device type
          502 — Device Registration API is unavailable
          500 — unexpected server error
      """
      if request.deviceType not in VALID_DEVICE_TYPES:
          raise HTTPException(
              status_code=400,
              detail=f"Invalid deviceType '{request.deviceType}'. "
                     f"Allowed values: {sorted(VALID_DEVICE_TYPES)}"
          )

      try:
          # httpx is an async HTTP client — forwards the request to the internal service
          async with httpx.AsyncClient() as client:
              response = await client.post(
                  f"{DEVICE_API_URL}/Device/register",
                  json={"userKey": request.userKey, "deviceType": request.deviceType},
                  timeout=5.0  # fail fast if the internal service is slow
              )

          if response.status_code != 200:
              raise HTTPException(
                  status_code=response.status_code,
                  detail="Device Registration API returned an error"
              )

          return {"statusCode": 200, "message": "Device registered successfully"}

      except httpx.RequestError:
          # Network-level error — the internal service is unreachable
          raise HTTPException(
              status_code=502,
              detail="Could not reach Device Registration API"
          )

      except HTTPException:
          raise

      except Exception as e:
          raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")