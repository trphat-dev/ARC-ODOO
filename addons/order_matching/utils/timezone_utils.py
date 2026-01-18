# -*- coding: utf-8 -*-
"""
Timezone utilities for Order Matching module.
Provides helper functions to format datetime values according to user's timezone.
"""

import pytz
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

# Default timezone khi user không có timezone được set
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'


def format_datetime_user_tz(env, dt, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Chuyển đổi datetime từ UTC sang timezone của user và format thành string.
    
    Odoo lưu datetime trong database dưới dạng UTC (naive datetime).
    Function này sẽ:
    1. Attach UTC timezone vào datetime
    2. Chuyển đổi sang timezone của user (từ env.user.tz hoặc context)
    3. Format thành string theo định dạng được chỉ định
    
    Args:
        env: Odoo environment (request.env hoặc self.env)
        dt: datetime object (naive, UTC) hoặc None
        fmt: Format string (default: '%Y-%m-%d %H:%M:%S')
    
    Returns:
        str: Formatted datetime string trong timezone của user, hoặc '' nếu dt là None/invalid
    
    Example:
        # Trong controller:
        from ..utils.timezone_utils import format_datetime_user_tz
        formatted_time = format_datetime_user_tz(request.env, order.create_date)
        
        # Trong model:
        formatted_time = format_datetime_user_tz(self.env, self.create_date)
    """
    if not dt:
        return ''
    
    try:
        # Nếu dt là string, parse thành datetime
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    dt = datetime.strptime(dt, '%Y-%m-%d')
                except ValueError:
                    return dt  # Return as-is if can't parse
        
        # Nếu không phải datetime, return empty
        if not isinstance(dt, datetime):
            return ''
        
        # Lấy timezone của user từ context hoặc user settings
        user_tz = None
        try:
            # Thử lấy từ context trước
            if env and hasattr(env, 'context') and env.context.get('tz'):
                user_tz = env.context.get('tz')
            # Fallback về user.tz
            elif env and hasattr(env, 'user') and env.user and env.user.tz:
                user_tz = env.user.tz
        except Exception:
            pass
        
        # Default timezone nếu không có
        if not user_tz:
            user_tz = DEFAULT_TIMEZONE
        
        # Attach UTC timezone vào datetime (Odoo lưu UTC nhưng naive)
        utc = pytz.UTC
        if dt.tzinfo is None:
            dt_utc = utc.localize(dt)
        else:
            dt_utc = dt.astimezone(utc)
        
        # Chuyển đổi sang user timezone
        try:
            local_tz = pytz.timezone(user_tz)
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            # Fallback về default timezone
            local_tz = pytz.timezone(DEFAULT_TIMEZONE)
            dt_local = dt_utc.astimezone(local_tz)
        
        # Format thành string
        return dt_local.strftime(fmt)
        
    except Exception as e:
        _logger.warning("Error formatting datetime to user timezone: %s", str(e))
        # Fallback: return UTC format nếu có lỗi
        try:
            if hasattr(dt, 'strftime'):
                return dt.strftime(fmt)
            return str(dt)
        except Exception:
            return ''


def format_date_user_tz(env, dt, fmt='%Y-%m-%d'):
    """
    Shortcut để format chỉ date (không có time) theo user timezone.
    
    Args:
        env: Odoo environment
        dt: datetime object hoặc date object
        fmt: Format string (default: '%Y-%m-%d')
    
    Returns:
        str: Formatted date string
    """
    return format_datetime_user_tz(env, dt, fmt)


def format_time_user_tz(env, dt, fmt='%H:%M:%S'):
    """
    Shortcut để format chỉ time (không có date) theo user timezone.
    
    Args:
        env: Odoo environment
        dt: datetime object
        fmt: Format string (default: '%H:%M:%S')
    
    Returns:
        str: Formatted time string
    """
    return format_datetime_user_tz(env, dt, fmt)
