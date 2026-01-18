def mround(value, step=50):
    """Excel-like MROUND: round value to nearest multiple of step."""
    try:
        step = float(step or 0)
        if step <= 0:
            return float(value or 0)
        return round(float(value or 0) / step) * step
    except Exception:
        return value

from . import const
from . import validators
from . import timezone_utils

__all__ = ['mround', 'const', 'validators', 'timezone_utils']

