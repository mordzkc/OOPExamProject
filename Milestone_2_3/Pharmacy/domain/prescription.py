import re
from enum import Enum

from ..config import PATIENT_ID_PATTERN
from .exceptions import ValidationError, InvalidQuantityError, InvalidStatusTransitionError


class PrescriptionStatus(Enum):
    PENDING = "pending"
    DISPENSED = "dispensed"
    CANCELLED = "cancelled"


_ALLOWED = {
    PrescriptionStatus.PENDING: {PrescriptionStatus.DISPENSED, PrescriptionStatus.CANCELLED},
    PrescriptionStatus.DISPENSED: set(),
    PrescriptionStatus.CANCELLED: set(),
}


class PrescriptionLine:
    """One medicine and quantity on a prescription."""

    def __init__(self, medicine_code: str, quantity: int):
        if not isinstance(medicine_code, str) or not medicine_code.strip():
            raise ValidationError("Prescription line needs a medicine code.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise InvalidQuantityError("Line quantity must be a whole number above zero.")
        self._medicine_code = medicine_code.strip().upper()
        self._quantity = quantity

    @property
    def medicine_code(self) -> str:
        return self._medicine_code

    @property
    def quantity(self) -> int:
        return self._quantity


class Prescription:
    """A prescription with one or more lines and a three-state status."""

    def __init__(self, patient_id, branch_id, prescriber_code=None,
                 status=PrescriptionStatus.PENDING, rx_id=None, lines=()):
        if not isinstance(patient_id, str) or not re.fullmatch(PATIENT_ID_PATTERN, patient_id.strip()):
            raise ValidationError("Patient id must look like PT-0001 (fictional identifiers only).")
        if not isinstance(branch_id, str) or not branch_id.strip():
            raise ValidationError("Prescription needs a branch.")
        self._id = rx_id
        self._patient_id = patient_id.strip()
        self._branch_id = branch_id.strip().upper()
        self._prescriber_code = prescriber_code.strip().upper() if isinstance(prescriber_code, str) \
            and prescriber_code.strip() else None
        self._status = status
        self._lines = []
        for line in lines:
            self._lines.append(line)

    @property
    def id(self):
        return self._id

    def assign_id(self, rx_id: int) -> None:
        self._id = rx_id

    @property
    def patient_id(self) -> str:
        return self._patient_id

    @property
    def branch_id(self) -> str:
        return self._branch_id

    @property
    def prescriber_code(self):
        return self._prescriber_code

    @property
    def status(self) -> PrescriptionStatus:
        return self._status

    @property
    def lines(self) -> tuple:
        return tuple(self._lines)

    def add_line(self, medicine_code: str, quantity: int) -> None:
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidStatusTransitionError("Lines can only be added to a pending prescription.")
        self._lines.append(PrescriptionLine(medicine_code, quantity))

    def _transition(self, target: PrescriptionStatus) -> None:
        if target not in _ALLOWED[self._status]:
            raise InvalidStatusTransitionError(
                f"Cannot change a {self._status.value} prescription to {target.value}.")
        self._status = target

    def ensure_dispensable(self) -> None:
        if self._status is not PrescriptionStatus.PENDING:
            raise InvalidStatusTransitionError(
                f"Prescription {self._id} is already {self._status.value}.")
        if not self._lines:
            raise ValidationError("Prescription has no lines.")

    def mark_dispensed(self) -> None:
        self._transition(PrescriptionStatus.DISPENSED)

    def cancel(self) -> None:
        self._transition(PrescriptionStatus.CANCELLED)
