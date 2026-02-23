# CI/CD Pipeline

Full pipeline: security scan → tests → build → integration tests → image scan.

## Triggers

- Push to `main`
- Pull requests to `main`
- Manual (workflow_dispatch)

## Pipeline Jobs

### Security Scan (source code)
- **Bandit** - SAST for Python (SQL injection, hardcoded secrets, etc)
- **Safety** - CVE check in requirements.txt
- **Hadolint** - Dockerfile linting
- **TruffleHog** - Secret detection in git history

### Unit Tests
- **statistics-api**: 19 tests, coverage report
- **device-registration-api**: 16 tests, coverage report
- Mocked DB and HTTP clients (no external dependencies)

### Docker Build
- Buildx with GitHub Actions Cache
- Tags: `latest` + commit SHA
- Saved as artifacts for next steps

### Integration Tests
- Full stack with docker-compose (postgres + both APIs)
- 7 end-to-end scenarios
- Tests the actual flow: POST → DB write → GET statistics

### Image Security Scan (Trivy)
- CVE scan on final Docker images
- Detects CRITICAL/HIGH/MEDIUM vulnerabilities
- Configured with `continue-on-error` (doesn't block, but logs everything)
- SARIF reports uploaded to GitHub Security tab

## Manual Trigger

```bash
# Via GitHub UI
https://github.com/geeanderson/device-statistics-api/actions
→ "CI/CD Pipeline" → "Run workflow"

# Via commit
git add .
git commit -m "trigger pipeline"
git push origin main
```

## Artifacts

Each run produces:
- `bandit-results/` - JSON reports
- `safety-results/` - JSON reports
- `hadolint-results/` - SARIF reports
- `coverage-*-api/` - HTML coverage reports
- `*-api-image` - Docker images as .tar (used by downstream jobs)

## GitHub Security Tab

SARIF reports from Hadolint and Trivy are auto-uploaded to:
https://github.com/geeanderson/device-statistics-api/security/code-scanning
