# Copyright 2024
# License AGPL-3.0 or later

"""
MROUND utility function - Excel-like rounding
"""


def mround(value, step=50):
    """Excel-like MROUND: round value to nearest multiple of step."""
    try:
        step = float(step or 0)
        if step <= 0:
            return float(value or 0)
        return round(float(value or 0) / step) * step
    except Exception:
        return value or 0

