# -*- coding: utf-8 -*-
"""
Constants for nav_management module.
Centralized configuration to avoid hardcoding values throughout the codebase.
"""

# Error handling
MAX_CONSECUTIVE_ERRORS = 5  # Maximum errors before breaking out of loops

# Date/Time formats
DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATE_FORMAT = '%d/%m/%Y'
DISPLAY_DATETIME_FORMAT = '%d/%m/%Y, %H:%M'

# NAV calculation
DEFAULT_MROUND_STEP = 50  # Default rounding step for price calculations
DAYS_PER_YEAR = 365  # Days used in interest calculations
DAYS_PER_MONTH = 30  # Approximate days per month

# Transaction statuses
class TransactionStatus:
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

# Inventory statuses
class InventoryStatus:
    DRAFT = 'draft'
    CONFIRMED = 'confirmed'
    COMPLETE = 'complete'

# NAV statuses
class NavStatus:
    ACTIVE = 'active'
    INACTIVE = 'inactive'

# Transaction types
class TransactionType:
    BUY = 'buy'
    SELL = 'sell'

# API Response keys
class ApiResponse:
    SUCCESS = 'success'
    ERROR = 'error'
    MESSAGE = 'message'
    DATA = 'data'

# Default values
DEFAULT_INTEREST_RATE = 0.0
DEFAULT_CCQ_QUANTITY = 0.0
DEFAULT_NAV_PRICE = 0.0
DEFAULT_TERM_MONTHS = 12
