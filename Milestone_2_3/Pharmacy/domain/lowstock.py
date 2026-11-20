from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    LOW = "LOW"
    CRITICAL = "CRITICAL"


def classify(quantity: int, reorder_level: int):
    """Return None if stock is healthy, otherwise Severity.LOW or Severity.CRITICAL."""
    if quantity > reorder_level:
        return None
    return Severity.CRITICAL if quantity * 2 <= reorder_level else Severity.LOW


def suggested_reorder(quantity: int, reorder_level: int) -> int:
    return max(2 * reorder_level - quantity, 0)


@dataclass(frozen=True)
class LowStockItem:
    branch_id: str
    medicine_code: str
    quantity: int
    reorder_level: int
    severity: Severity
    suggested_reorder: int


@dataclass(frozen=True)
class StockLevel:
    """One row of the stock screen: a stock item joined with its medicine details."""
    branch_id: str
    medicine_code: str
    medicine_name: str
    quantity: int
    reorder_level: int
    severity: "Severity | None"   # None means healthy
