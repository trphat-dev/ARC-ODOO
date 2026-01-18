# Copyright 2024
# License AGPL-3.0 or later

"""
MROUND utility function - Round with <25 down, >=25 up threshold (step 50)
"""

import math


def mround(value, step=50):
    """
    Round with custom threshold: <25 round down, >=25 round up (for step=50).
    This replaces the standard Excel MROUND with custom rounding logic.
    
    Examples:
        mround(1024) = 1000 (24 < 25 -> down)
        mround(1025) = 1050 (25 >= 25 -> up)
        mround(1049) = 1050 (49 >= 25 -> up)
    """
    try:
        num = float(value or 0)
        step = float(step or 50)
        if step <= 0:
            return num
        
        remainder = num % step
        threshold = step / 2  # 25 when step = 50
        
        if remainder < threshold:
            # Below threshold -> round down
            return (num // step) * step
        else:
            # At or above threshold -> round up
            return math.ceil(num / step) * step
    except Exception:
        return value


# Alias for backward compatibility
mround25 = mround
