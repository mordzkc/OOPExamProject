from datetime import datetime

from .exceptions import ValidationError


class AuditEntry:
    """One logged action: who did what, when (fictional staff ids only). Extension."""

    def __init__(self, staff_id: str, action: str, detail: str = "", timestamp: str = None):
        if not isinstance(staff_id, str) or not staff_id.strip():
            raise ValidationError("Audit entry needs a staff id.")
        if not isinstance(action, str) or not action.strip():
            raise ValidationError("Audit entry needs an action.")
        self._staff_id = staff_id.strip().upper()
        self._action = action.strip().upper()
        self._detail = detail or ""
        self._timestamp = timestamp or datetime.now().isoformat(timespec="seconds")

    @property
    def timestamp(self) -> str:
        return self._timestamp

    @property
    def staff_id(self) -> str:
        return self._staff_id

    @property
    def action(self) -> str:
        return self._action

    @property
    def detail(self) -> str:
        return self._detail
