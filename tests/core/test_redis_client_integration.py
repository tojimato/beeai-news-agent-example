"""Integration tests for Redis client with actual connection.

These tests require a running Redis instance configured via REDIS_URL env var.
They are skipped if Redis is unavailable and should only run in development/
staging environments.
"""

import pytest
import redis

from src.core.redis_client import RedisClient
from src.config.settings import REDIS_URL


def _redis_available() -> bool:
    """Check if Redis is available at configured REDIS_URL.

    Uses REDIS_URL environment variable. Returns False if connection fails
    or env var not set.

    Returns:
        bool: True if Redis is reachable, False otherwise.
    """
    try:
        test_client = redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=2,
            decode_responses=True
        )
        test_client.ping()
        return True
    except (redis.ConnectionError, redis.RedisError, Exception):
        return False


class TestRedisClientIntegration:
    """Integration tests with actual Redis connection (requires Redis running)."""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Reset singleton before and after each test."""
        RedisClient._instance = None
        RedisClient._pool = None
        yield
        RedisClient._instance = None
        RedisClient._pool = None

    @pytest.mark.skipif(
        not _redis_available(),
        reason="Redis not available at configured REDIS_URL"
    )
    def test_real_redis_connection(self):
        """Connect to real Redis instance and verify singleton."""
        client = RedisClient.get_instance()

        # Should be Redis instance
        assert isinstance(client, redis.Redis)

        # Should get same instance on second call
        client2 = RedisClient.get_instance()
        assert client is client2

    @pytest.mark.skipif(
        not _redis_available(),
        reason="Redis not available at configured REDIS_URL"
    )
    def test_real_redis_operations(self):
        """Test actual Redis operations through client."""
        client = RedisClient.get_instance()

        # Test SET/GET
        test_key = "test_integration_key"
        test_value = "test_value_123"

        client.set(test_key, test_value)
        result = client.get(test_key)

        assert result == test_value

        # Cleanup
        client.delete(test_key)

    @pytest.mark.skipif(
        not _redis_available(),
        reason="Redis not available at configured REDIS_URL"
    )
    def test_real_redis_health_check(self):
        """Test health check with real connection."""
        # Should succeed if Redis is running
        is_healthy = RedisClient.is_healthy()
        assert is_healthy is True

    @pytest.mark.skipif(
        not _redis_available(),
        reason="Redis not available at configured REDIS_URL"
    )
    def test_real_redis_close_and_reconnect(self):
        """Test closing pool and reconnecting."""
        client1 = RedisClient.get_instance()
        client1.set("test_key", "value1")

        # Close pool
        RedisClient.close()

        # Reconnect and verify works
        client2 = RedisClient.get_instance()
        result = client2.get("test_key")

        assert result == "value1"

        # Cleanup
        client2.delete("test_key")


# Helper function removed - defined above before class
