  # Public-facing API that receives login events and returns device statistics.
  # This service is the entry point for external traffic.
  # It calls the Device Registration API internally to persist data.

  from fastapi import FastAPI, HTTPException, Query
  from fastapi.responses import JSONResponse
  from pydantic import BaseModel
  import httpx
  import psycopg2
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
          return JSONResponse(
              status_code=400,
              content={"statusCode": 400, "message": "bad_request"}
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
              return JSONResponse(
                status_code=400,
                content={"statusCode": 400, "message": "bad_request"}
              )

          return {"statusCode": 200, "message": "success"}

      except httpx.RequestError:
          # Network-level error — the internal service is unreachable
          return JSONResponse(
            status_code=400,
            content={"statusCode": 400, "message": "bad_request"}
          )

      except Exception as e:
          return JSONResponse(
            status_code=400,
            content={"statusCode": 400, "message": "bad_request"}
        )


  @app.get("/Log/auth/statistics")
  def get_statistics(deviceType: str = Query(..., description="Device type to filter by")):
      """
      Returns how many times a device type was registered.
      Expects a deviceType query param (iOS, Android, Watch or TV).

      Returns:
        200 — {"deviceType": "...", "count": N} on success
        200 — {"deviceType": "...", "count": -1} on error (invalid type or DB error)
      """
      if deviceType not in VALID_DEVICE_TYPES:
          return {"deviceType": deviceType, "count": -1}

      conn = None
      try:
          conn = get_db_connection()
          cursor = conn.cursor()

          # Parameterized query — %s placeholder prevents SQL injection
          cursor.execute(
              "SELECT COUNT(*) FROM device_registrations WHERE device_type = %s",
              (deviceType,)
          )
          count = cursor.fetchone()[0]

          return {"deviceType": deviceType, "count": count}

      except Exception as e:
          return {"deviceType": deviceType, "count": -1}

      finally:
          if conn:
              conn.close()
