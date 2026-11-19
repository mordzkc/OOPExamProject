from .exceptions import ValidationError


class Branch:
    """A dispensing point such as Main Campus or a satellite clinic."""

    def __init__(self, branch_id: str, name: str, location: str = ""):
        if not isinstance(branch_id, str) or not branch_id.strip():
            raise ValidationError("Branch id is required.")
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("Branch name is required.")
        self._branch_id = branch_id.strip().upper()
        self._name = name.strip()
        self._location = (location or "").strip()

    @property
    def branch_id(self) -> str:
        return self._branch_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def location(self) -> str:
        return self._location
