import math
from abc import ABC, abstractmethod

from ..config import CONTROLLED_MAX_PER_LINE, NARCOTIC_MAX_PER_LINE
from .exceptions import (ValidationError, InvalidPriceError, InvalidQuantityError,
                         UnauthorisedPrescriberError, QuantityLimitError)


class Medicine(ABC):
    """Abstract base: shared identity, price and reorder rules."""
    CATEGORY = "ABSTRACT"

    def __init__(self, code: str, name: str, unit_price: float, reorder_level: int):
        if not isinstance(code, str) or not code.strip():
            raise ValidationError("Medicine code is required.")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Medicine name is required.")
        self._code = code.strip().upper()
        self._name = name.strip()
        self.unit_price = unit_price
        self.reorder_level = reorder_level

    @property
    def code(self) -> str:
        return self._code

    @property
    def category(self) -> str:
        return self.CATEGORY

    @property
    def name(self) -> str:
        return self._name

    @property
    def unit_price(self) -> float:
        return self._unit_price

    @unit_price.setter
    def unit_price(self, value) -> None:
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0):
            raise InvalidPriceError(f"Unit price must be a positive number, got {value!r}.")
        self._unit_price = float(value)

    @property
    def reorder_level(self) -> int:
        return self._reorder_level

    @reorder_level.setter
    def reorder_level(self, value) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValidationError(f"Reorder level must be a whole number >= 0, got {value!r}.")
        self._reorder_level = value

    @property
    @abstractmethod
    def max_quantity_per_line(self):
        """Largest quantity allowed on one prescription line, or None for no limit."""

    @abstractmethod
    def validate_dispense(self, quantity: int, prescriber_code, allow_list) -> None:
        """Raise a PharmacyError if this medicine cannot be dispensed as requested."""

    def _check_positive(self, quantity) -> None:
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError("Quantity must be a whole number above zero.")


class OrdinaryMedicine(Medicine):
    CATEGORY = "ORDINARY"

    @property
    def max_quantity_per_line(self):
        return None

    def validate_dispense(self, quantity, prescriber_code, allow_list):
        self._check_positive(quantity)


class ControlledMedicine(Medicine):
    CATEGORY = "CONTROLLED"
    MAX_PER_LINE = CONTROLLED_MAX_PER_LINE

    @property
    def max_quantity_per_line(self):
        return self.MAX_PER_LINE

    def validate_dispense(self, quantity, prescriber_code, allow_list):
        self._check_positive(quantity)
        if not allow_list.is_authorised(prescriber_code):
            raise UnauthorisedPrescriberError(
                f"Prescriber {prescriber_code!r} is not authorised to receive {self.name}.")
        if quantity > self.max_quantity_per_line:
            raise QuantityLimitError(
                f"{self.name}: at most {self.max_quantity_per_line} units per line, got {quantity}.")


class NarcoticMedicine(ControlledMedicine):
    CATEGORY = "NARCOTIC"
    MAX_PER_LINE = NARCOTIC_MAX_PER_LINE
    is_high_alert = True

    def validate_dispense(self, quantity, prescriber_code, allow_list):
        super().validate_dispense(quantity, prescriber_code, allow_list)
        # Extension hook: a pharmacist co-signature check would be added here.


_CLASSES = {c.CATEGORY: c for c in (OrdinaryMedicine, ControlledMedicine, NarcoticMedicine)}


def medicine_class_for(category: str):
    try:
        return _CLASSES[str(category).strip().upper()]
    except KeyError:
        raise ValidationError(f"Unknown medicine category {category!r}.") from None


def medicine_from_row(row) -> Medicine:
    cls = medicine_class_for(row["category"])
    return cls(row["code"], row["name"], row["unit_price"], row["reorder_level"])
