from ..config import DEFAULT_CAPACITY
from .exceptions import InvalidQuantityError, CapacityExceededError, InsufficientStockError


def _check_qty(qty, what):
    if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0:
        raise InvalidQuantityError(f"Quantity to {what} must be a whole number above zero.")


class StockItem:
    """Quantity of one medicine at one branch. Never negative, never above capacity."""

    def __init__(self, branch_id, medicine_code, quantity=0, max_capacity=DEFAULT_CAPACITY):
        self._branch_id = branch_id
        self._medicine_code = medicine_code
        self._max_capacity = max_capacity
        self._quantity = 0
        if quantity:
            self.add(quantity)

    @property
    def branch_id(self):
        return self._branch_id

    @property
    def medicine_code(self):
        return self._medicine_code

    @property
    def max_capacity(self):
        return self._max_capacity

    @property
    def quantity(self) -> int:
        return self._quantity

    def add(self, qty: int) -> None:
        _check_qty(qty, "receive")
        if self._quantity + qty > self._max_capacity:
            raise CapacityExceededError(
                f"Capacity is {self._max_capacity}; holding {self._quantity}, cannot add {qty}.")
        self._quantity += qty

    def remove(self, qty: int) -> None:
        _check_qty(qty, "remove")
        if qty > self._quantity:
            raise InsufficientStockError(f"Only {self._quantity} in stock, {qty} requested.")
        self._quantity -= qty
