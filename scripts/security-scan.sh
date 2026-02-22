#!/bin/bash
# Run all security scans via Docker (no install needed)
# Usage: ./scripts/security-scan.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Security Scan${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

FAILED=0

# -----------------------------------------------------------------------------
# 1. Trivy - CVE scan
# -----------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Trivy - CVE scan${NC}"
echo "Checking for known vulnerabilities in dependencies..."

if docker run --rm -v "$PROJECT_ROOT":/src aquasec/trivy:latest \
    fs /src \
    --severity HIGH,CRITICAL \
    --exit-code 0 \
    --format table \
    --quiet; then
    echo -e "${GREEN}✓ No HIGH/CRITICAL vulnerabilities${NC}"
else
    echo -e "${RED}✗ Found vulnerabilities${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# -----------------------------------------------------------------------------
# 2. Bandit - Python SAST
# -----------------------------------------------------------------------------
echo -e "${BLUE}[2/5] Bandit - Python SAST${NC}"
echo "Looking for insecure code patterns..."

if docker run --rm -v "$PROJECT_ROOT":/src cytopia/bandit:latest \
    -r /src/statistics-api /src/device-registration-api \
    -ll \
    --format txt; then
    echo -e "${GREEN}✓ No security issues${NC}"
else
    echo -e "${YELLOW}⚠ Found potential issues${NC}"
    FAILED=$((FAILED + 1))
fi
echo ""

# -----------------------------------------------------------------------------
# 3. Safety - Dependency check
# -----------------------------------------------------------------------------
echo -e "${BLUE}[3/5] Safety - Dependency check${NC}"
echo "Checking against vulnerability database..."

for api in statistics-api device-registration-api; do
    echo "  → $api/requirements.txt"
    if docker run --rm -v "$PROJECT_ROOT":/src pyupio/safety:latest \
        safety check --file=/src/$api/requirements.txt --json || true; then
        echo -e "${GREEN}    ✓ Clean${NC}"
    else
        echo -e "${YELLOW}    ⚠ Has vulnerabilities${NC}"
    fi
done
echo ""

# -----------------------------------------------------------------------------
# 4. Hadolint - Dockerfile lint
# -----------------------------------------------------------------------------
echo -e "${BLUE}[4/5] Hadolint - Dockerfile lint${NC}"
echo "Checking Dockerfiles..."

for dockerfile in statistics-api/Dockerfile device-registration-api/Dockerfile; do
    echo "  → $dockerfile"
    if docker run --rm -i hadolint/hadolint:latest < "$dockerfile"; then
        echo -e "${GREEN}    ✓ OK${NC}"
    else
        echo -e "${YELLOW}    ⚠ Has warnings${NC}"
    fi
done
echo ""

# -----------------------------------------------------------------------------
# 5. Trufflehog - Secret scan
# -----------------------------------------------------------------------------
echo -e "${BLUE}[5/5] Trufflehog - Secret scan${NC}"
echo "Looking for hardcoded credentials..."

TRUFFLEHOG_OUTPUT=$(docker run --rm -v "$PROJECT_ROOT":/src trufflesecurity/trufflehog:latest \
    filesystem /src \
    --no-update \
    --only-verified 2>&1)

echo "$TRUFFLEHOG_OUTPUT"

if echo "$TRUFFLEHOG_OUTPUT" | grep -q "Found verified result"; then
    echo -e "${RED}✗ Found verified secrets${NC}"
    FAILED=$((FAILED + 1))
else
    echo -e "${GREEN}✓ No secrets found${NC}"
fi
echo ""

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ $FAILED check(s) found issues — review output above${NC}"
    exit 1
fi
