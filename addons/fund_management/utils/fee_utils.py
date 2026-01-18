# Copyright 2024
# License AGPL-3.0 or later

"""
Fee calculation utilities
"""
from . import mround
from .constants import (
    FEE_THRESHOLD_1, FEE_THRESHOLD_2,
    FEE_RATE_1, FEE_RATE_2, FEE_RATE_3,
    MROUND_STEP
)


def calculate_fee(amount):
    """
    Calculate fee based on amount thresholds
    
    Args:
        amount: Transaction amount
        
    Returns:
        float: Calculated fee (rounded to MROUND_STEP)
    """
    amount = float(amount or 0.0)
    
    if amount < FEE_THRESHOLD_1:
        fee = amount * FEE_RATE_1
    elif amount < FEE_THRESHOLD_2:
        fee = amount * FEE_RATE_2
    else:
        fee = amount * FEE_RATE_3
    
    return mround.mround(fee, MROUND_STEP)

