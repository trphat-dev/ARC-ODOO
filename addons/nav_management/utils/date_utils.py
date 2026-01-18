# Copyright 2024
# License AGPL-3.0 or later

"""
Date utility functions for NAV calculations
"""
from datetime import datetime, timedelta


def workday(start_date, days, holidays=None):
    """
    Excel WORKDAY function: Returns a date that is a specified number of working days 
    before or after a start date, excluding weekends and optionally holidays.
    
    Args:
        start_date: Start date (date or datetime)
        days: Number of working days (negative for past, positive for future)
        holidays: Optional list of holiday dates to exclude
    
    Returns:
        date: Result date
    """
    if not start_date:
        return None
    
    # Convert to date if datetime
    if isinstance(start_date, datetime):
        current_date = start_date.date()
    else:
        current_date = start_date
    
    if holidays is None:
        holidays = []
    
    # Convert holidays to date set for fast lookup
    holiday_set = set()
    for h in holidays:
        if isinstance(h, datetime):
            holiday_set.add(h.date())
        else:
            holiday_set.add(h)
    
    step = 1 if days >= 0 else -1
    remaining_days = abs(days)
    
    while remaining_days > 0:
        current_date += timedelta(days=step)
        
        # Skip weekends (Saturday=5, Sunday=6)
        weekday = current_date.weekday()
        if weekday >= 5:  # Saturday or Sunday
            continue
        
        # Skip holidays
        if current_date in holiday_set:
            continue
        
        remaining_days -= 1
    
    return current_date


def weekday(date_value, return_type=2):
    """
    Excel WEEKDAY function: Returns the day of the week as a number.
    
    Args:
        date_value: Date or datetime
        return_type: 
            1 = Sunday=1, Saturday=7 (default Excel)
            2 = Monday=1, Sunday=7 (ISO standard)
            3 = Monday=0, Sunday=6
    
    Returns:
        int: Day of week (1-7 for return_type 1 or 2, 0-6 for return_type 3)
    """
    if not date_value:
        return None
    
    # Convert to date if datetime
    if isinstance(date_value, datetime):
        date_obj = date_value.date()
    else:
        date_obj = date_value
    
    # Python weekday: Monday=0, Sunday=6
    python_weekday = date_obj.weekday()
    
    if return_type == 1:
        # Sunday=1, Saturday=7
        return python_weekday + 2 if python_weekday < 6 else 1
    elif return_type == 2:
        # Monday=1, Sunday=7 (ISO standard)
        return python_weekday + 1
    elif return_type == 3:
        # Monday=0, Sunday=6
        return python_weekday
    else:
        # Default to return_type=2
        return python_weekday + 1


def next_weekday(date_value):
    """
    Get next weekday (Monday-Friday) from given date.
    If date is Saturday/Sunday, return next Monday.
    
    Args:
        date_value: Date or datetime
    
    Returns:
        date: Next weekday
    """
    if not date_value:
        return None
    
    if isinstance(date_value, datetime):
        date_obj = date_value.date()
    else:
        date_obj = date_value
    
    weekday_num = weekday(date_obj, return_type=2)
    
    if weekday_num > 5:  # Saturday or Sunday
        # Move to next Monday
        days_to_add = 8 - weekday_num
        return date_obj + timedelta(days=days_to_add)
    
    return date_obj

