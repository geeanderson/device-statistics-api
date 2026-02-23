#!/usr/bin/env python3
# tests/integration/test_e2e.py
# End-to-end integration tests for the full stack

import requests
import time
import sys

# Base URL for the Statistics API (public endpoint)
BASE_URL = "http://localhost:8000"

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(message):
    """Print test name"""
    print(f"\n{YELLOW}TEST:{RESET} {message}")

def print_pass(message):
    """Print success message"""
    print(f"{GREEN}✓{RESET} {message}")

def print_fail(message):
    """Print failure message"""
    print(f"{RED}✗{RESET} {message}")

def wait_for_api(max_retries=30, delay=2):
    """Wait for the API to be ready"""
    print(f"\n{YELLOW}Waiting for API to be ready...{RESET}")
    for i in range(max_retries):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print_pass(f"API is ready after {i * delay} seconds")
                return True
        except requests.exceptions.RequestException:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                print_fail(f"API did not become ready after {max_retries * delay} seconds")
                return False
    return False

def test_health_check():
    """Test GET /health endpoint"""
    print_test("Health check endpoint")

    response = requests.get(f"{BASE_URL}/health")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
    assert data["service"] == "statistics-api", f"Expected service 'statistics-api', got {data.get('service')}"

    print_pass("Health check passed")

def test_post_valid_devices():
    """Test POST /Log/auth with valid device types"""
    print_test("POST /Log/auth - valid device types")

    test_cases = [
        {"userKey": "user-integration-001", "deviceType": "iOS"},
        {"userKey": "user-integration-002", "deviceType": "Android"},
        {"userKey": "user-integration-003", "deviceType": "Watch"},
        {"userKey": "user-integration-004", "deviceType": "TV"},
    ]

    for payload in test_cases:
        response = requests.post(f"{BASE_URL}/Log/auth", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code} for {payload}"
        data = response.json()
        assert data["statusCode"] == 200, f"Expected statusCode 200, got {data.get('statusCode')}"
        assert data["message"] == "success", f"Expected message 'success', got {data.get('message')}"
        print_pass(f"  {payload['deviceType']}: {payload['userKey']} registered successfully")

def test_post_invalid_devices():
    """Test POST /Log/auth with invalid device types"""
    print_test("POST /Log/auth - invalid device types")

    test_cases = [
        {"userKey": "user-invalid-001", "deviceType": "Windows"},
        {"userKey": "user-invalid-002", "deviceType": "Linux"},
        {"userKey": "user-invalid-003", "deviceType": "Tablet"},
    ]

    for payload in test_cases:
        response = requests.post(f"{BASE_URL}/Log/auth", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code} for {payload}"
        data = response.json()
        assert data["statusCode"] == 400, f"Expected statusCode 400, got {data.get('statusCode')}"
        assert data["message"] == "bad_request", f"Expected message 'bad_request', got {data.get('message')}"
        print_pass(f"  {payload['deviceType']}: correctly rejected")

def test_get_statistics():
    """Test GET /Log/auth/statistics endpoint"""
    print_test("GET /Log/auth/statistics - valid queries")

    # We registered 1 iOS, 1 Android, 1 Watch, 1 TV in test_post_valid_devices
    expected_counts = {
        "iOS": 1,
        "Android": 1,
        "Watch": 1,
        "TV": 1,
    }

    for device_type, expected_count in expected_counts.items():
        response = requests.get(f"{BASE_URL}/Log/auth/statistics?deviceType={device_type}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code} for {device_type}"
        data = response.json()
        assert data["deviceType"] == device_type, f"Expected deviceType {device_type}, got {data.get('deviceType')}"
        assert data["count"] == expected_count, f"Expected count {expected_count} for {device_type}, got {data.get('count')}"
        print_pass(f"  {device_type}: count = {data['count']}")

def test_get_statistics_invalid():
    """Test GET /Log/auth/statistics with invalid device type"""
    print_test("GET /Log/auth/statistics - invalid device type")

    response = requests.get(f"{BASE_URL}/Log/auth/statistics?deviceType=Windows")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["deviceType"] == "Windows", f"Expected deviceType 'Windows', got {data.get('deviceType')}"
    assert data["count"] == -1, f"Expected count -1 for invalid type, got {data.get('count')}"
    print_pass("Invalid device type returns count -1")

def test_multiple_registrations_same_user():
    """Test multiple registrations from the same user"""
    print_test("POST /Log/auth - same user, multiple times")

    payload = {"userKey": "user-multi-reg", "deviceType": "iOS"}

    # Register the same user 3 times
    for i in range(3):
        response = requests.post(f"{BASE_URL}/Log/auth", json=payload)
        assert response.status_code == 200, f"Registration {i+1} failed"
        data = response.json()
        assert data["statusCode"] == 200
        assert data["message"] == "success"

    print_pass("Same user registered 3 times successfully")

    # Check statistics - should now have 1 (from test_post_valid_devices) + 3 = 4
    response = requests.get(f"{BASE_URL}/Log/auth/statistics?deviceType=iOS")
    data = response.json()
    assert data["count"] == 4, f"Expected count 4, got {data['count']}"
    print_pass(f"iOS count updated correctly: {data['count']}")

def test_data_persistence():
    """Test that data persists across API calls"""
    print_test("Data persistence across requests")

    # Register a new device
    payload = {"userKey": "user-persistence-test", "deviceType": "Android"}
    response = requests.post(f"{BASE_URL}/Log/auth", json=payload)
    assert response.status_code == 200

    # Query statistics - should include the new registration
    response = requests.get(f"{BASE_URL}/Log/auth/statistics?deviceType=Android")
    data = response.json()
    # Should be at least 2 (1 from test_post_valid_devices + 1 from this test)
    assert data["count"] >= 2, f"Expected count >= 2, got {data['count']}"
    print_pass(f"Android count: {data['count']} (persistence confirmed)")

def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Integration Tests - End-to-End")
    print("=" * 60)

    # Wait for API to be ready
    if not wait_for_api():
        print_fail("API failed to start. Aborting tests.")
        sys.exit(1)

    tests = [
        test_health_check,
        test_post_valid_devices,
        test_post_invalid_devices,
        test_get_statistics,
        test_get_statistics_invalid,
        test_multiple_registrations_same_user,
        test_data_persistence,
    ]

    failed_tests = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print_fail(f"FAILED: {test.__name__}")
            print(f"  Error: {e}")
            failed_tests.append(test.__name__)
        except Exception as e:
            print_fail(f"ERROR: {test.__name__}")
            print(f"  Error: {e}")
            failed_tests.append(test.__name__)

    # Summary
    print("\n" + "=" * 60)
    total_tests = len(tests)
    passed_tests = total_tests - len(failed_tests)

    if failed_tests:
        print(f"{RED}FAILED{RESET}: {len(failed_tests)}/{total_tests} tests failed")
        print(f"Failed tests: {', '.join(failed_tests)}")
        sys.exit(1)
    else:
        print(f"{GREEN}SUCCESS{RESET}: All {total_tests} integration tests passed ✓")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
