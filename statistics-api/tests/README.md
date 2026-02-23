# Statistics API - Unit Tests

## Running Tests

```bash
# Install deps
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=. --cov-report=term --cov-report=html

# Specific test
pytest tests/test_main.py::TestLogAuthEndpoint::test_log_auth_valid_device_success -v
```

## Coverage

Target: **70% minimum**

View HTML report:
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # macOS
```

## Test Organization

- **TestHealthEndpoint** - /health checks
- **TestLogAuthEndpoint** - POST /Log/auth (mocked httpx)
- **TestGetStatisticsEndpoint** - GET /Log/auth/statistics (mocked DB)
- **TestInputValidation** - Input validation logic
