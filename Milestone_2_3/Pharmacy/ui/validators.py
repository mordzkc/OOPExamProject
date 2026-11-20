"""Turn raw text from tkinter Entry widgets into clean Python values.

Entry widgets always return strings. The domain classes are strict (a price must be a number), so the
presentation layer converts text first and raises the same ValidationError the domain uses. That way every
problem, wherever it is detected, reaches the user as one clear message.
"""
from ..domain.exceptions import InvalidPriceError, ValidationError


def required(text, label: str) -> str:
    """Return the trimmed text or raise if it is empty."""
    value = (text or "").strip()
    if not value:
        raise ValidationError(f"{label} is required.")
    return value


def parse_price(text) -> float:
    """'1,200' -> 1200.0. The domain then checks that the number is above zero."""
    value = required(text, "Unit price")
    try:
        return float(value.replace(",", ""))
    except ValueError:
        raise InvalidPriceError(f"Unit price must be a number, got {value!r}.") from None


def parse_whole_number(text, label: str) -> int:
    """'25' -> 25. Rejects blanks, decimals and words."""
    value = required(text, label)
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f"{label} must be a whole number, got {value!r}.") from None


def code_from_choice(choice: str, label: str) -> str:
    """'PCM500 - Paracetamol 500mg' -> 'PCM500'. Used for combobox values."""
    return required(choice, label).split(" - ")[0].strip()
