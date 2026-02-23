# Integration Tests

End-to-end tests against the full stack (postgres + both APIs).

## What's Tested

| Test | Validates |
|------|-----------|
| `test_health_check` | /health endpoint works |
| `test_post_valid_devices` | iOS, Android, Watch, TV registration |
| `test_post_invalid_devices` | Rejects Windows, Linux, Tablet |
| `test_get_statistics` | Correct counts returned |
| `test_get_statistics_invalid` | Returns count -1 for invalid types |
| `test_multiple_registrations_same_user` | Same user can register multiple times |
| `test_data_persistence` | Data persists across requests |

## Running Locally

```bash
# Start stack
docker compose up --build -d

# Wait ~10s for health checks, then:
pip install -r tests/integration/requirements.txt
python tests/integration/test_e2e.py

# Cleanup
docker compose down -v
```

## CI/CD Usage

In GitHub Actions, we use pre-built images from artifacts:

```bash
docker load --input /tmp/statistics-api.tar
docker load --input /tmp/device-registration-api.tar
docker compose -f docker-compose.ci.yml up -d
python tests/integration/test_e2e.py
docker compose -f docker-compose.ci.yml down -v
```

## Expected Output

```
============================================================
Integration Tests - End-to-End
============================================================

Waiting for API to be ready...
✓ API is ready after 4 seconds

TEST: Health check endpoint
✓ Health check passed

TEST: POST /Log/auth - valid device types
✓   iOS: user-integration-001 registered successfully
...

============================================================
SUCCESS: All 7 integration tests passed ✓
============================================================
```

## Troubleshooting

**API not ready?**
```bash
docker compose ps
docker compose logs statistics-api
```

**Connection refused?**
```bash
lsof -i :8000  # check if port is in use
docker ps      # check if containers are running
```
