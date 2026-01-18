import logging
from enum import Enum


_logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    ENTER_LONG = "enter_long"
    EXIT_LONG = "exit_long"
    ENTER_SHORT = "enter_short"
    EXIT_SHORT = "exit_short"


class SignalDirection(str, Enum):
    LONG = "long"
    SHORT = "short"


class ExitType(str, Enum):
    ROI = "roi"
    STOP_LOSS = "stop_loss"
    EXIT_SIGNAL = "exit_signal"
    OTHER = "other"


class TradingSignal:
    """Lightweight signal container used across predictions/orders."""

    def __init__(
        self,
        signal_type: SignalType,
        direction: SignalDirection = SignalDirection.LONG,
        strength: float = 0.5,
        exit_type: ExitType = ExitType.EXIT_SIGNAL,
        confidence: float = 0.0,
        reason: str = "",
        **metadata,
    ):
        self.signal_type = signal_type
        self.direction = direction
        self.strength = max(0.0, min(1.0, float(strength)))
        self.exit_type = exit_type
        self.confidence = max(0.0, min(100.0, float(confidence)))
        self.reason = reason
        self.metadata = metadata

    @property
    def is_entry(self):
        return self.signal_type in (SignalType.ENTER_LONG, SignalType.ENTER_SHORT)

    @property
    def is_exit(self):
        return self.signal_type in (SignalType.EXIT_LONG, SignalType.EXIT_SHORT)

    @property
    def is_long(self):
        return self.direction == SignalDirection.LONG

    def to_dict(self):
        return {
            "signal_type": self.signal_type.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "exit_type": self.exit_type.value,
            "confidence": self.confidence,
            "reason": self.reason,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data):
        try:
            signal_type = SignalType(data.get("signal_type", "enter_long"))
            direction = SignalDirection(data.get("direction", "long"))
            exit_type = ExitType(data.get("exit_type", "exit_signal"))
            strength = float(data.get("strength", 0.5))
            confidence = float(data.get("confidence", 0.0))
            reason = data.get("reason", "")
            known = {"signal_type", "direction", "strength", "exit_type", "confidence", "reason"}
            metadata = {k: v for k, v in data.items() if k not in known}
            return cls(signal_type, direction, strength, exit_type, confidence, reason, **metadata)
        except Exception as exc:  # pragma: no cover - defensive
            _logger.warning("Failed to parse TradingSignal dict: %s", exc, exc_info=True)
            return None


def create_entry_signal(direction=SignalDirection.LONG, strength=0.5, confidence=0.0, reason="", **metadata):
    return TradingSignal(SignalType.ENTER_LONG if direction == SignalDirection.LONG else SignalType.ENTER_SHORT,
                         direction=direction,
                         strength=strength,
                         confidence=confidence,
                         reason=reason,
                         **metadata)


def create_exit_signal(direction=SignalDirection.LONG, exit_type=ExitType.EXIT_SIGNAL,
                       strength=0.5, confidence=0.0, reason="", **metadata):
    return TradingSignal(SignalType.EXIT_LONG if direction == SignalDirection.LONG else SignalType.EXIT_SHORT,
                         direction=direction,
                         strength=strength,
                         exit_type=exit_type,
                         confidence=confidence,
                         reason=reason,
                         **metadata)


def create_signal_from_legacy(buy_signal=False, sell_signal=False, confidence=0.0, reason=""):
    """Convert legacy buy/sell signals to TradingSignal objects."""
    if buy_signal:
        return create_entry_signal(
            direction=SignalDirection.LONG,
            strength=min(1.0, confidence / 100.0) if confidence else 0.5,
            confidence=confidence,
            reason=reason or "Buy signal",
        )
    if sell_signal:
        return create_exit_signal(
            direction=SignalDirection.LONG,
            strength=min(1.0, confidence / 100.0) if confidence else 0.5,
            confidence=confidence,
            reason=reason or "Sell signal",
        )
    return None

