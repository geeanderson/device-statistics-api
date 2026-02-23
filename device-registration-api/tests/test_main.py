# Unit tests for the Device Registration API endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, VALID_DEVICE_TYPES

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_check_returns_ok(self):
        """Health endpoint should return 200 with correct service name"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "device-registration-api"}


class TestRegisterDeviceEndpoint:
    """Tests for POST /Device/register"""

    @patch('main.get_db_connection')
    def test_register_device_valid_input(self, mock_db_conn):
        """Valid device registration should return statusCode 200"""
        # Mock database connection and cursor
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        response = client.post(
            "/Device/register",
            json={"userKey": "user123", "deviceType": "iOS"}
        )

        assert response.status_code == 200
        assert response.json() == {"statusCode": 200}

        # Verify database operations were called
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_register_device_invalid_device_type(self):
        """Invalid device type should return statusCode 400"""
        response = client.post(
            "/Device/register",
            json={"userKey": "user123", "deviceType": "Windows"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400}

    def test_register_device_empty_user_key(self):
        """Empty userKey should return statusCode 400"""
        response = client.post(
            "/Device/register",
            json={"userKey": "", "deviceType": "iOS"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400}

    def test_register_device_whitespace_user_key(self):
        """Whitespace-only userKey should return statusCode 400"""
        response = client.post(
            "/Device/register",
            json={"userKey": "   ", "deviceType": "Android"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400}

    @patch('main.get_db_connection')
    def test_register_device_database_error(self, mock_db_conn):
        """Database error should return statusCode 400"""
        # Mock database connection that raises an error
        mock_cursor = Mock()
        mock_cursor.execute.side_effect = Exception("Database error")

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        response = client.post(
            "/Device/register",
            json={"userKey": "user123", "deviceType": "iOS"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400}

        # Verify rollback was called
        mock_conn.rollback.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('main.get_db_connection')
    def test_register_device_trims_whitespace(self, mock_db_conn):
        """UserKey with leading/trailing whitespace should be trimmed"""
        # Mock database connection and cursor
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        response = client.post(
            "/Device/register",
            json={"userKey": "  user123  ", "deviceType": "Watch"}
        )

        assert response.status_code == 200
        assert response.json() == {"statusCode": 200}

        # Verify execute was called with trimmed userKey
        call_args = mock_cursor.execute.call_args
        assert call_args[0][1] == ("user123", "Watch")


class TestInputValidation:
    """Tests for input validation logic"""

    def test_all_valid_device_types_accepted(self):
        """All valid device types should be accepted (with mocked DB)"""
        with patch('main.get_db_connection') as mock_db_conn:
            mock_cursor = Mock()
            mock_conn = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_db_conn.return_value = mock_conn

            for device_type in VALID_DEVICE_TYPES:
                response = client.post(
                    "/Device/register",
                    json={"userKey": "user123", "deviceType": device_type}
                )
                assert response.status_code == 200
                assert response.json() == {"statusCode": 200}

    def test_missing_fields_returns_422(self):
        """Missing required fields should return 422 (FastAPI validation)"""
        # Missing deviceType
        response = client.post(
            "/Device/register",
            json={"userKey": "user123"}
        )
        assert response.status_code == 422

        # Missing userKey
        response = client.post(
            "/Device/register",
            json={"deviceType": "iOS"}
        )
        assert response.status_code == 422

        # Empty payload
        response = client.post(
            "/Device/register",
            json={}
        )
        assert response.status_code == 422


class TestDatabaseInteraction:
    """Tests for database interaction logic"""

    @patch('main.get_db_connection')
    def test_sql_injection_prevention(self, mock_db_conn):
        """SQL injection attempts should be prevented by parameterized queries"""
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        # Attempt SQL injection
        malicious_key = "user'; DROP TABLE device_registrations; --"

        response = client.post(
            "/Device/register",
            json={"userKey": malicious_key, "deviceType": "iOS"}
        )

        # Should still process normally with parameterized query
        assert response.status_code == 200

        # Verify execute was called with parameters (not string interpolation)
        call_args = mock_cursor.execute.call_args
        assert "%s" in call_args[0][0]  # Query uses placeholders
        assert malicious_key.strip() in call_args[0][1]  # Actual value passed as parameter
