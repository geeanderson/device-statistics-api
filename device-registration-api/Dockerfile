# ---------------------------------------------------------------------------
# Builds the container image for the internal Device Registration API.
# This service is NOT exposed to external traffic — it only receives
# requests from the Statistics API over the internal Docker/K8s network.
# Non-root user (appuser) runs the process
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Base image
# ---------------------------------------------------------------------------
FROM python:3.11-slim

# ---------------------------------------------------------------------------
# Working directory
# ---------------------------------------------------------------------------
WORKDIR /app

# ---------------------------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------------------------
COPY requirements.txt .

# ---------------------------------------------------------------------------
# --no-cache-dir: do not store the download cache inside the image
#   keeping the final image smaller
# ---------------------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Copy application code
# ---------------------------------------------------------------------------
COPY main.py .

# ---------------------------------------------------------------------------
# Security: run as non-root user
# chown transfers ownership of /app to appuser so the process can read
# the source files — without this, Python raises PermissionError on startup.
# ---------------------------------------------------------------------------
RUN adduser --system --no-create-home appuser && chown -R appuser /app
USER appuser

# ---------------------------------------------------------------------------
# Expose the port service
# ---------------------------------------------------------------------------
EXPOSE 8001

# ---------------------------------------------------------------------------
# Start the application
# --host 0.0.0.0 : listen on all interfaces inside the container
# --port 8001    : must correspond to the service of exposing the port
# ---------------------------------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
