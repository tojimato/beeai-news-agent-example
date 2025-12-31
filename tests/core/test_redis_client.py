"""Tests for Redis connection pool client."""

import pytest
import redis
from unittest.mock import patch, MagicMock

from src.core.redis_client import RedisClient


class TestRedisClientSingleton:
    """Test Redis client singleton pattern and connection pooling."""

    def teardown_method(self):
        """Reset singleton after each test."""
        RedisClient._instance = None
        RedisClient._pool = None

    def test_get_instance_creates_singleton(self):
        """First call to get_instance creates pool and client."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            instance1 = RedisClient.get_instance()
            instance2 = RedisClient.get_instance()

            # Both calls return same instance
            assert instance1 is instance2
            # Pool created only once
            assert mock_pool.call_count == 1

    def test_get_instance_configures_pool_correctly(self):
        """Pool is configured with correct parameters."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            RedisClient.get_instance()

            # Verify pool configuration
            mock_pool.assert_called_once()
            call_kwargs = mock_pool.call_args[1]
            assert call_kwargs['max_connections'] == 20
            assert call_kwargs['socket_connect_timeout'] == 5
            assert call_kwargs['socket_keepalive'] is True
            assert call_kwargs['health_check_interval'] == 30
            assert call_kwargs['decode_responses'] is True

    def test_get_instance_tests_connection(self):
        """get_instance initializes pool without testing connection upfront."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            instance = RedisClient.get_instance()

            # Pool initialized
            assert instance is not None
            # Connection lazy-validated on first use (via health checks)
            mock_pool.assert_called_once()

    def test_get_instance_raises_on_pool_init_error(self):
        """Raises ConnectionError if pool initialization fails."""
        with patch(
            'src.core.redis_client.ConnectionPool.from_url',
            side_effect=Exception("Pool init failed")
        ):
            with pytest.raises(redis.ConnectionError):
                RedisClient.get_instance()

    def test_close_disconnects_pool(self):
        """close() disconnects all connections in pool."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            RedisClient.get_instance()
            RedisClient.close()

            # Pool.disconnect() called
            mock_pool_instance.disconnect.assert_called_once()
            # Singleton reset
            assert RedisClient._instance is None
            assert RedisClient._pool is None

    def test_close_is_idempotent(self):
        """close() can be called multiple times safely."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance

            RedisClient.get_instance()
            RedisClient.close()
            # Should not raise on second call
            RedisClient.close()

    def test_close_handles_exceptions(self):
        """close() handles exceptions gracefully."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            mock_pool_instance = MagicMock()
            mock_pool.return_value = mock_pool_instance
            # Make disconnect raise exception
            mock_pool_instance.disconnect.side_effect = Exception("Disconnect failed")

            RedisClient.get_instance()
            # Should not raise
            RedisClient.close()

    def test_is_healthy_returns_true_when_connected(self):
        """is_healthy() returns True when Redis is reachable."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            with patch.object(redis.Redis, 'ping') as mock_ping:
                mock_pool_instance = MagicMock()
                mock_pool.return_value = mock_pool_instance
                mock_ping.return_value = True

                result = RedisClient.is_healthy()

                assert result is True

    def test_is_healthy_returns_false_on_error(self):
        """is_healthy() returns False when Redis is unavailable."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            with patch.object(
                redis.Redis,
                'ping',
                side_effect=redis.ConnectionError()
            ):
                mock_pool_instance = MagicMock()
                mock_pool.return_value = mock_pool_instance

                result = RedisClient.is_healthy()

                assert result is False

    def test_is_healthy_handles_redis_error(self):
        """is_healthy() handles RedisError gracefully."""
        with patch('src.core.redis_client.ConnectionPool.from_url') as mock_pool:
            with patch.object(
                redis.Redis,
                'ping',
                side_effect=redis.RedisError("Generic error")
            ):
                mock_pool_instance = MagicMock()
                mock_pool.return_value = mock_pool_instance

                result = RedisClient.is_healthy()

                assert result is False
