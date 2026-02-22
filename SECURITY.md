# Security Scanning

We run security scans with Trivy, Bandit, Safety, Hadolint, and Trufflehog. Nothing fancy — just catching CVEs and dumb mistakes before they hit production.

---

## Quick start

Security scanning is optional if you're just testing the APIs. But if you're developing or want to see what we check for, you have three options:

1. **Manual scan** — runs everything in Docker, no install needed
2. **Pre-commit hooks** — scans before you commit (opt-in)

---

## Tools

| Tool | What it does |
|------|--------------|
| **Trivy** | Finds CVEs in Python deps and OS packages |
| **Bandit** | Catches insecure Python code (SQL injection, etc) |
| **Safety** | Checks PyPI packages against vulnerability database |
| **Hadolint** | Lints Dockerfiles for security issues |
| **Trufflehog** | Finds API keys and passwords you forgot to remove |

---

## Option 1: Manual scan

Easiest way to run all checks. Only needs Docker running.

```bash
./scripts/security-scan.sh
```

Takes about 30 seconds. Output looks like:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Security Scan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[1/5] Trivy - CVE scan
✓ No HIGH/CRITICAL vulnerabilities

[2/5] Bandit - Python SAST
✓ No security issues

[3/5] Safety - Dependency check
✓ All dependencies clean

[4/5] Hadolint - Dockerfile lint
✓ Both Dockerfiles OK

[5/5] Trufflehog - Secret scan
✓ No hardcoded secrets

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ All checks passed
```

Exit code 0 = clean, 1 = issues found.

---

## Option 2: Pre-commit hooks

Runs scans automatically before each commit. Catches issues before you push.

### Setup

```bash
pip install pre-commit
pre-commit install
```

Done. Now every commit runs the checks.

### What happens

- **HIGH/CRITICAL** vulns → blocks the commit
- **LOW/MEDIUM** → shows warning, lets you commit

### Skip if needed

```bash
git commit --no-verify -m "hotfix"
```

Use sparingly. Don't make it a habit.

### First run is slow

Pre-commit downloads tools on first use (~2-3 min). After that it's fast (5-10 sec per commit).

---

## Security policy

We block on HIGH and CRITICAL, warn on everything else.

| Severity | What we do |
|----------|------------|
| CRITICAL | Block commit/merge |
| HIGH | Block commit/merge |
| MEDIUM | Warn, allow |
| LOW | Warn, allow |

### False positives

Sometimes tools flag things that aren't actually issues.

**Trivy:** Add the CVE to `.trivyignore`

**Bandit:** Add `# nosec` with a comment explaining why it's safe

```python
# Safe because we validate input first
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))  # nosec B608
```

**detect-secrets:** Update `.secrets.baseline`

---

## Common problems

### Pre-commit hooks aren't running

```bash
pre-commit uninstall
pre-commit install
pre-commit run --all-files  # test it
```

### Trivy is slow

First run downloads the vulnerability DB (~200MB). After that it's cached.

Pre-download it:
```bash
docker run --rm aquasec/trivy image --download-db-only
```

### Hadolint complains about valid Dockerfile

Ignore specific rules inline:

```dockerfile
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y package-name
```

---

## Generate SBOM

For audits or compliance:

```bash
# statistics-api
docker run --rm -v "$PWD":/src aquasec/trivy \
  fs /src/statistics-api \
  --format cyclonedx \
  --output /src/statistics-api-sbom.json

# device-registration-api
docker run --rm -v "$PWD":/src aquasec/trivy \
  fs /src/device-registration-api \
  --format cyclonedx \
  --output /src/device-registration-api-sbom.json
```

---

## Tips

Run the scan before pushing:
```bash
./scripts/security-scan.sh && git push
```

Keep deps up to date:
```bash
pip list --outdated
pip install --upgrade <package>
```

Never commit secrets. If you do accidentally:
- Rotate the credential immediately
- Don't just delete it from the file — it's still in git history
- Use `git filter-repo` or BFG to scrub history if needed

Don't ignore scan results blindly. If you suppress a warning, document why in a comment or `.trivyignore`.

---

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Trivy docs](https://aquasecurity.github.io/trivy/)
- [Bandit docs](https://bandit.readthedocs.io/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
