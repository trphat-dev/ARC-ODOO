# -*- coding: utf-8 -*-
"""
Rate Limiting Utility for ARC-FMS API Endpoints

In-memory sliding window rate limiter. Suitable for single-process deployments.
For multi-process/production, replace with Redis-backed implementation.

Usage:
    from odoo.addons.arc_core.utils.rate_limiter import rate_limit

    @http.route('/api/example', type='json', auth='user')
    @rate_limit(max_calls=30, period=60)
    def my_endpoint(self, **kwargs):
        ...
"""

import time
import threading
import functools
import logging
from collections import defaultdict

from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# Thread-safe storage: {key: [timestamp1, timestamp2, ...]}
_rate_store = defaultdict(list)
_rate_lock = threading.Lock()

# Cleanup interval: remove expired entries every N seconds
_CLEANUP_INTERVAL = 300  # 5 minutes
_last_cleanup = time.time()


def _cleanup_expired(period):
    """Remove expired timestamps from the rate store."""
    global _last_cleanup
    now = time.time()
    if now - _last_cleanup < _CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    cutoff = now - period
    keys_to_delete = []
    for key, timestamps in _rate_store.items():
        _rate_store[key] = [t for t in timestamps if t > cutoff]
        if not _rate_store[key]:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del _rate_store[key]


def _get_client_key(key_func=None):
    """Get a unique key for the current client."""
    if key_func:
        return key_func()

    # Prefer user ID if authenticated, otherwise IP
    try:
        if request and request.env and request.env.user:
            user_id = request.env.user.id
            if user_id and user_id > 1:  # Not public user
                return f"user:{user_id}"
    except Exception:
        pass

    # Fallback to IP address
    try:
        ip = request.httprequest.remote_addr or 'unknown'
        return f"ip:{ip}"
    except Exception:
        return "unknown"


def rate_limit(max_calls=30, period=60, key_func=None, error_message=None):
    """
    Rate limiting decorator for Odoo HTTP controllers.

    Args:
        max_calls: Maximum number of calls allowed within the period.
        period: Time window in seconds (default: 60s = 1 minute).
        key_func: Optional callable that returns a custom key for rate limiting.
                  Default: uses user ID if authenticated, else IP address.
        error_message: Optional custom error message when rate limited.

    Examples:
        # 30 requests per minute (default)
        @rate_limit()

        # 5 requests per minute for sensitive operations
        @rate_limit(max_calls=5, period=60)

        # 100 requests per minute for read-heavy endpoints
        @rate_limit(max_calls=100, period=60)
    """
    if error_message is None:
        error_message = 'Too many requests. Please try again later.'

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client_key = _get_client_key(key_func)
            endpoint = getattr(func, '__name__', 'unknown')
            rate_key = f"{client_key}:{endpoint}"

            now = time.time()
            cutoff = now - period

            with _rate_lock:
                # Clean up old entries
                _cleanup_expired(period)

                # Get timestamps for this client+endpoint
                timestamps = _rate_store[rate_key]

                # Remove expired timestamps
                timestamps = [t for t in timestamps if t > cutoff]
                _rate_store[rate_key] = timestamps

                if len(timestamps) >= max_calls:
                    _logger.warning(
                        "[RATE LIMIT] Client %s exceeded %d/%ds on %s",
                        client_key, max_calls, period, endpoint
                    )

                    # Return appropriate error response
                    try:
                        # For type='json' routes
                        return {
                            'success': False,
                            'error': 'rate_limited',
                            'message': error_message,
                        }
                    except Exception:
                        return Response(
                            '{"error": "rate_limited", "message": "Too many requests"}',
                            status=429,
                            content_type='application/json'
                        )

                # Record this request
                timestamps.append(now)
                _rate_store[rate_key] = timestamps

            return func(*args, **kwargs)

        return wrapper
    return decorator


def rate_limit_strict(max_calls=5, period=60):
    """
    Strict rate limiting for sensitive operations (login, OTP, payment).
    Lower limits, logs at ERROR level.
    """
    return rate_limit(
        max_calls=max_calls,
        period=period,
        error_message='Too many attempts. Please wait before trying again.'
    )
