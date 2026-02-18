# Device Statistics API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Manifests-326CE5?logo=kubernetes&logoColor=white)

---

## What is this?

Two backend APIs to handle device authentication events and track usage statistics per device type.

When a user authenticates from a device, that event gets logged. You can then query how many registrations happened per device type (iOS, Android, Watch, TV). Two services handle this — one public-facing, one internal — backed by a PostgreSQL database.

---

## Architecture

```
                       External Traffic
                              |
                              v
                   +---------------------+
                   |   Statistics API    |  ← public (port 8000)
                   |   POST /Log/auth    |
                   |   GET  /Log/auth/   |
                   |        statistics   |
                   +---------------------+
                              |
                   (internal network only)
                              |
                              v
                   +---------------------+
                   | Device Registration |  ← internal only
                   |       API           |
                   |  POST /Device/      |
                   |       register      |
                   +---------------------+
                              |
                              v
                   +---------------------+
                   |    PostgreSQL 16     |
                   +---------------------+
```

External clients only talk to the Statistics API on port 8000. That service handles the request and calls the Device Registration API internally. The registration service is never exposed outside.

---

## Tech Stack

| Technology     | Role                                        |
|----------------|---------------------------------------------|
| Python 3.11    | Application runtime                         |
| FastAPI        | Web framework for both APIs                 |
| psycopg2       | PostgreSQL driver (raw SQL, no ORM)         |
| httpx          | HTTP client for inter-service communication |
| PostgreSQL 16  | Relational database                         |
| Docker Compose | Local development stack                     |
| Kubernetes     | Production deployment                       |

---

## Project Structure

```
device-statistics-api/
├── statistics-api/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── device-registration-api/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── k8s/                   # Kubernetes manifests
├── terraform/             # Infrastructure as Code
├── docker-compose.yml
├── init.sql
└── README.md
```

---

## Running locally

The only requirement is Docker Desktop installed and running. No need to install Python or PostgreSQL on your machine.

**1. Clone the repository**

```bash
git clone <repo-url>
cd device-statistics-api
```

**2. Set up environment variables**

```bash
cp .env.example .env
```

The `.env.example` already has the right values for Docker Compose. Open `.env` and change `DB_PASSWORD` to anything you want — just keep it consistent.

**3. Start the stack**

```bash
docker compose up --build
```

The first run takes a few minutes while it builds the images. On the next runs it's much faster.

Wait until you see `Application startup complete` in the logs from both APIs. That means everything is ready.

> If you see a database connection error right after startup, don't worry — it usually means one of the APIs started before PostgreSQL was fully ready. Docker Compose handles the restart automatically.

**4. Stopping the environment**

```bash
# Stop without losing your data
docker compose down

# Stop and wipe the database (clean slate)
docker compose down -v
```

---

## Testing the APIs

All requests go through port 8000 (Statistics API). The registration API runs on port 8001 but is internal — you don't call it directly.

FastAPI also generates interactive docs. If you prefer a browser instead of curl, open:
- http://localhost:8000/docs

### Health check

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "service": "statistics-api"}
```

### Log a device authentication event

```bash
curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-123", "deviceType": "iOS"}'
```

```json
{"statusCode": 200, "message": "Device registered successfully"}
```

Run a few more to have some data to query:

```bash
curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-456", "deviceType": "Android"}'

curl -X POST http://localhost:8000/Log/auth \
  -H "Content-Type: application/json" \
  -d '{"userKey": "user-789", "deviceType": "iOS"}'
```

Valid device types: `iOS`, `Android`, `Watch`, `TV`. Anything else returns a 400 error.

### Query statistics

```bash
curl "http://localhost:8000/Log/auth/statistics?deviceType=iOS"
```

```json
{"deviceType": "iOS", "count": 2}
```

---

## API Reference

### Statistics API — port 8000

| Method | Path                   | Description                           |
|--------|------------------------|---------------------------------------|
| GET    | /health                | Health check                          |
| POST   | /Log/auth              | Log a device authentication event     |
| GET    | /Log/auth/statistics   | Get registration count by device type |

**POST /Log/auth** — request body:

```json
{
  "userKey": "string",
  "deviceType": "iOS | Android | Watch | TV"
}
```

**GET /Log/auth/statistics** — query param: `?deviceType=iOS`

### Device Registration API — port 8001 (internal only)

| Method | Path               | Description                          |
|--------|--------------------|--------------------------------------|
| GET    | /health            | Health check                         |
| POST   | /Device/register   | Save a device registration to the DB |

This API is not accessible from outside. In Docker Compose it lives on an internal network. In Kubernetes it will be a ClusterIP service with no external exposure.

---

## Security

- No credentials in code — everything goes through environment variables
- SQL queries use parameterized statements (no SQL injection risk)
- The registration API is not reachable from outside
- Containers run as non-root users
- Kubernetes deployments will include resource limits and health probes

---

## License

MIT
