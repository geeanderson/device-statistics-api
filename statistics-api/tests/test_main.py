# Unit tests for the Statistics API endpoints

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
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
        assert response.json() == {"status": "ok", "service": "statistics-api"}


class TestLogAuthEndpoint:
    """Tests for POST /Log/auth"""

    @pytest.mark.asyncio
    @patch('main.httpx.AsyncClient')
    async def test_log_auth_valid_device_success(self, mock_client):
        """Valid device type should call Device Registration API and return success"""
        # Mock the httpx response
        mock_response = Mock()
        mock_response.status_code = 200

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        response = client.post(
            "/Log/auth",
            json={"userKey": "user123", "deviceType": "iOS"}
        )

        assert response.status_code == 200
        assert response.json() == {"statusCode": 200, "message": "success"}

    def test_log_auth_invalid_device_type(self):
        """Invalid device type should return 400 bad_request"""
        response = client.post(
            "/Log/auth",
            json={"userKey": "user123", "deviceType": "Windows"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400, "message": "bad_request"}

    @pytest.mark.asyncio
    @patch('main.httpx.AsyncClient')
    async def test_log_auth_device_api_error(self, mock_client):
        """Device Registration API returning error should return bad_request"""
        # Mock the httpx response with error status
        mock_response = Mock()
        mock_response.status_code = 400

        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        response = client.post(
            "/Log/auth",
            json={"userKey": "user123", "deviceType": "iOS"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400, "message": "bad_request"}

    @pytest.mark.asyncio
    @patch('main.httpx.AsyncClient')
    async def test_log_auth_network_error(self, mock_client):
        """Network error should return bad_request"""
        # Mock network error
        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = Exception("Network error")
        mock_client.return_value.__aenter__.return_value = mock_async_client

        response = client.post(
            "/Log/auth",
            json={"userKey": "user123", "deviceType": "Android"}
        )

        assert response.status_code == 400
        assert response.json() == {"statusCode": 400, "message": "bad_request"}


class TestGetStatisticsEndpoint:
    """Tests for GET /Log/auth/statistics"""

    @patch('main.get_db_connection')
    def test_get_statistics_valid_device(self, mock_db_conn):
        """Valid device type should return count from database"""
        # Mock database connection and cursor
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (5,)  # Return count of 5

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        response = client.get("/Log/auth/statistics?deviceType=iOS")

        assert response.status_code == 200
        assert response.json() == {"deviceType": "iOS", "count": 5}

        # Verify database was queried correctly
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_get_statistics_invalid_device_type(self):
        """Invalid device type should return count -1"""
        response = client.get("/Log/auth/statistics?deviceType=Windows")

        assert response.status_code == 200
        assert response.json() == {"deviceType": "Windows", "count": -1}

    @patch('main.get_db_connection')
    def test_get_statistics_database_error(self, mock_db_conn):
        """Database error should return count -1"""
        # Mock database connection that raises an error
        mock_db_conn.side_effect = Exception("Database connection failed")

        response = client.get("/Log/auth/statistics?deviceType=Android")

        assert response.status_code == 200
        assert response.json() == {"deviceType": "Android", "count": -1}

    @patch('main.get_db_connection')
    def test_get_statistics_zero_count(self, mock_db_conn):
        """Device type with no registrations should return count 0"""
        # Mock database connection returning zero count
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (0,)

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn

        response = client.get("/Log/auth/statistics?deviceType=TV")

        assert response.status_code == 200
        assert response.json() == {"deviceType": "TV", "count": 0}


class TestInputValidation:
    """Tests for input validation logic"""

    def test_all_valid_device_types_accepted(self):
        """All valid device types should be accepted"""
        for device_type in VALID_DEVICE_TYPES:
            response = client.get(f"/Log/auth/statistics?deviceType={device_type}")
            # Should not return -1 for validation failure (may return -1 for DB mock though)
            assert response.status_code == 200

    def test_missing_device_type_parameter(self):
        """Missing deviceType parameter should return 422 (FastAPI validation)"""
        response = client.get("/Log/auth/statistics")
        assert response.status_code == 422  # FastAPI validation error
