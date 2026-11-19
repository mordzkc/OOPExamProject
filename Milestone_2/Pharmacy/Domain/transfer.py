from .exceptions import ValidationError, InvalidQuantityError


class StockTransfer:
    """A request to move stock of one medicine between two branches. Extension."""

    def __init__(self, from_branch: str, to_branch: str, medicine_code: str, quantity: int):
        self._from_branch = str(from_branch).strip().upper()
        self._to_branch = str(to_branch).strip().upper()
        self._medicine_code = str(medicine_code).strip().upper()
        self._quantity = quantity
        self.validate()

    @property
    def from_branch(self) -> str:
        return self._from_branch

    @property
    def to_branch(self) -> str:
        return self._to_branch

    @property
    def medicine_code(self) -> str:
        return self._medicine_code

    @property
    def quantity(self) -> int:
        return self._quantity

    def validate(self) -> None:
        if self._from_branch == self._to_branch:
            raise ValidationError("A transfer needs two different branches.")
        if isinstance(self._quantity, bool) or not isinstance(self._quantity, int) or self._quantity <= 0:
            raise InvalidQuantityError("Transfer quantity must be a whole number above zero.")
