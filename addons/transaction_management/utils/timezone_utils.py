# -*- coding: utf-8 -*-
"""
Timezone Utilities for Transaction Management
Ensures datetime fields are displayed in User's Timezone (default Asia/Ho_Chi_Minh).
"""

from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)

def format_datetime_user_tz(env, dt, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Convert UTC datetime to user's configured timezone.
    Fallback to Asia/Ho_Chi_Minh if no user timezone set.
    
    Args:
        env: Odoo Environment
        dt: datetime object (naive UTC expected from Odoo) or string
        fmt: format string
    """
    if not dt:
        return ''
    
    try:
        # 1. Parse string if needed
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    dt = datetime.strptime(dt, '%Y-%m-%d')
                except ValueError:
                    return dt
        
        if not isinstance(dt, datetime):
            return str(dt)

        # 2. Determine User Timezone
        user_tz = 'Asia/Ho_Chi_Minh'
        try:
            if env and hasattr(env, 'context') and env.context.get('tz'):
                user_tz = env.context.get('tz')
            elif env and hasattr(env, 'user') and env.user and env.user.tz:
                user_tz = env.user.tz
        except Exception:
            pass
            
        if not user_tz:
            user_tz = 'Asia/Ho_Chi_Minh'

        # 3. Localize UTC
        if dt.tzinfo is None:
            dt_utc = pytz.UTC.localize(dt)
        else:
            dt_utc = dt.astimezone(pytz.UTC)
            
        # 4. Convert to User TZ
        try:
            local_tz = pytz.timezone(user_tz)
            dt_local = dt_utc.astimezone(local_tz)
        except Exception:
            # Fallback to VN if timezone invalid
            local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            dt_local = dt_utc.astimezone(local_tz)
            
        return dt_local.strftime(fmt)
        
    except Exception as e:
        _logger.warning(f"Error formatting user tz: {e}")
        try:
            return dt.strftime(fmt)
        except:
            return str(dt)

def format_date_user_tz(env, dt, fmt='%Y-%m-%d'):
    """
    Shortcut for date formatting with user timezone
    """
    return format_datetime_user_tz(env, dt, fmt)
