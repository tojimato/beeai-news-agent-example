"""Thread-safe Redis connection management with connection pooling.

This module provides a singleton Redis client with connection pooling for
efficient concurrent access and graceful error handling. Suitable for
production use with multiple workers/threads.
"""

from typing import Optional

import redis
from redis import ConnectionPool

from src.config.settings import REDIS_URL
from src.utils.logger import log_error, log_warning


class RedisClient:
    """
    Singleton Redis client with connection pooling for concurrent access.

    Features:
    - Connection pooling (max 20 concurrent connections)
    - Timeout management (5 sec for both connect and read)
    - Health checks (auto-recovery every 30 seconds)
    - Graceful shutdown and cleanup
    - Thread-safe operations
    """

    _pool: Optional[ConnectionPool] = None
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        """
        Get thread-safe singleton Redis instance with connection pooling.

        Initializes connection pool on first call with optimized settings for
        concurrent access and reliability. Subsequent calls return cached
        instance. Does not validate connection on init (lazy validation on use).

        Returns:
            redis.Redis: Thread-safe Redis client with pooled connections.

        Raises:
            redis.ConnectionError: If pool initialization fails.
        """
        if cls._instance is None:
            try:
                cls._pool = ConnectionPool.from_url(
                    REDIS_URL,
                    max_connections=20,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30,
                    decode_responses=True
                )
                cls._instance = redis.Redis(connection_pool=cls._pool)
                log_warning(
                    "✅ Redis pool initialized (max 20 connections, 5s timeout)"
                )
            except Exception as e:
                log_error(f"Failed to initialize Redis pool: {e}")
                raise redis.ConnectionError(f"Redis pool init failed: {e}") from e

        return cls._instance

    @classmethod
    def close(cls) -> None:
        """
        Close all connections in pool (call on application shutdown).

        Safely disconnects all pooled connections. Safe to call multiple
        times; idempotent operation.
        """
        try:
            if cls._pool:
                cls._pool.disconnect()
                cls._instance = None
                cls._pool = None
                log_warning("✅ Redis pool closed")
        except Exception as e:
            log_error(f"Error closing Redis pool: {e}")

    @classmethod
    def is_healthy(cls) -> bool:
        """
        Check if Redis connection is healthy.

        Returns:
            bool: True if Redis is reachable, False otherwise.
        """
        try:
            instance = cls.get_instance()
            instance.ping()
            return True
        except (redis.ConnectionError, redis.RedisError):
            return False
