# -*- coding: utf-8 -*-
"""
Timezone Utilities for Fund Management
Ensures created_at and date_end fields use Asia/Ho_Chi_Minh timezone correctly.
"""

from datetime import datetime, timedelta
import pytz
import logging

_logger = logging.getLogger(__name__)

# Default timezone for Vietnam
VIETNAM_TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')
UTC_TIMEZONE = pytz.UTC


def get_vietnam_now():
    """
    Get current datetime in Asia/Ho_Chi_Minh timezone.
    Returns: datetime object with Vietnam timezone
    """
    return datetime.now(VIETNAM_TIMEZONE)


def get_vietnam_now_utc():
    """
    Get current datetime in UTC, but calculated from Vietnam timezone.
    Use this when storing Odoo Datetime fields (which expect UTC).
    Returns: datetime object in UTC
    """
    vietnam_now = datetime.now(VIETNAM_TIMEZONE)
    return vietnam_now.astimezone(UTC_TIMEZONE).replace(tzinfo=None)


def to_vietnam_tz(dt):
    """
    Convert a datetime to Asia/Ho_Chi_Minh timezone.
    If naive datetime, assumes it's UTC.
    Args:
        dt: datetime object
    Returns: datetime object with Vietnam timezone
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = UTC_TIMEZONE.localize(dt)
    return dt.astimezone(VIETNAM_TIMEZONE)


def to_utc(dt):
    """
    Convert a datetime to UTC timezone.
    If naive datetime, assumes it's Vietnam timezone.
    Args:
        dt: datetime object
    Returns: datetime object in UTC (naive, for Odoo storage)
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume naive datetime is Vietnam timezone
        dt = VIETNAM_TIMEZONE.localize(dt)
    return dt.astimezone(UTC_TIMEZONE).replace(tzinfo=None)


def calculate_date_end(start_date, term_months):
    """
    Calculate date_end based on start_date + term_months.
    Returns datetime in UTC for Odoo storage.
    Args:
        start_date: datetime object (created_at)
        term_months: int (number of months)
    Returns: datetime object in UTC
    """
    if start_date is None or not term_months:
        return None
    
    # Convert to Vietnam timezone for calculation
    if start_date.tzinfo is None:
        start_date = UTC_TIMEZONE.localize(start_date)
    
    start_vietnam = start_date.astimezone(VIETNAM_TIMEZONE)
    
    # Add months
    year = start_vietnam.year
    month = start_vietnam.month + int(term_months)
    
    while month > 12:
        month -= 12
        year += 1
    
    # Handle day overflow (e.g., Jan 31 + 1 month -> Feb 28)
    day = start_vietnam.day
    while True:
        try:
            end_vietnam = start_vietnam.replace(year=year, month=month, day=day)
            break
        except ValueError:
            day -= 1
            if day < 1:
                day = 1
                break
    
    # Return as UTC for Odoo storage
    return end_vietnam.astimezone(UTC_TIMEZONE).replace(tzinfo=None)


def format_vietnam_datetime(dt, fmt='%d/%m/%Y %H:%M:%S'):
    """
    Format a datetime for display in Vietnam timezone.
    Args:
        dt: datetime object
        fmt: format string (default: dd/mm/yyyy HH:MM:SS)
    Returns: formatted string
    """
    if dt is None:
        return '--'
    vietnam_dt = to_vietnam_tz(dt)
    return vietnam_dt.strftime(fmt)


def format_vietnam_date(dt, fmt='%d/%m/%Y'):
    """
    Format a date for display in Vietnam timezone.
    Args:
        dt: datetime or date object
        fmt: format string (default: dd/mm/yyyy)
    Returns: formatted string
    """
    if dt is None:
        return '--'
    if hasattr(dt, 'tzinfo'):
        vietnam_dt = to_vietnam_tz(dt)
        return vietnam_dt.strftime(fmt)
    # Check if object has strftime
    if hasattr(dt, 'strftime'):
        return dt.strftime(fmt)
    return str(dt)


# Convenience function for models
def set_created_at_vietnam():
    """
    Get created_at value for new records.
    Returns datetime in UTC for Odoo storage.
    """
    return get_vietnam_now_utc()


def set_date_end_vietnam(created_at, term_months):
    """
    Calculate and return date_end in UTC for Odoo storage.
    Args:
        created_at: datetime (UTC naive from Odoo)
        term_months: int
    Returns: datetime in UTC
    """
    return calculate_date_end(created_at, term_months)


# ==========================================
# Dynamic User Timezone Support (New)
# ==========================================

def format_datetime_user_tz(env, dt, fmt='%Y-%m-%d %H:%M:%S'):
    """
    Convert UTC datetime to user's configured timezone.
    Fallback to Asia/Ho_Chi_Minh if no user timezone set.
    
    Args:
        env: Odoo Environment
        dt: datetime object (naive UTC expected from Odoo)
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
