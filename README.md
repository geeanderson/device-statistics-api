# Device Statistics API

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Manifests-326CE5?logo=kubernetes&logoColor=white)

---

## What is this?

This project provides two backend APIs to handle device authentication events and track usage statistics per device type.

The idea is simple: whenever a user authenticates from a device, that event gets logged. From there, you can query how many registrations happened per device type. Two separate services handle this — one public-facing, one internal — backed by a PostgreSQL database.

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
                   | Device Registration |  ← internal (port 8001)
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

External clients talk only to the Statistics API. That service handles the incoming request and calls the Device Registration API internally to persist the event. The registration service is never exposed outside the cluster.

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

## API Endpoints

### Statistics API — port 8000 (public)

| Method | Path                 | Description                              |
|--------|----------------------|------------------------------------------|
| GET    | /health              | Health check                             |
| POST   | /Log/auth            | Log a device authentication event        |
| GET    | /Log/auth/statistics | Get registration count by device type    |

### Device Registration API — port 8001 (internal)

| Method | Path             | Description                        |
|--------|------------------|------------------------------------|
| GET    | /health          | Health check                       |
| POST   | /Device/register | Save a device registration to the DB |

Accepted device types: `iOS`, `Android`, `Watch`, `TV`

---

## Running locally

The full stack (both APIs + database) runs via Docker Compose:

```bash
cp .env.example .env
# fill in the variables in .env
docker compose up --build
```

---

## Security

A few things worth noting on the security side:

- No credentials in code — everything goes through environment variables
- SQL queries use parameterized statements throughout (no string concatenation)
- The registration API is isolated and not reachable from outside the cluster
- Containers run as non-root users
- Kubernetes deployments include resource limits and health probes

---

## License

MIT
