import unittest

from pharmacy.domain.audit import AuditEntry
from pharmacy.domain.exceptions import ValidationError, InvalidQuantityError
from pharmacy.domain.medicine import NarcoticMedicine, OrdinaryMedicine
from pharmacy.domain.transfer import StockTransfer


class ExtensionClasses(unittest.TestCase):
    def test_audit_entry(self):
        e = AuditEntry("st-01", "dispense", "rx:1")
        self.assertEqual((e.staff_id, e.action, e.detail), ("ST-01", "DISPENSE", "rx:1"))
        with self.assertRaises(ValidationError):
            AuditEntry("", "DISPENSE")

    def test_stock_transfer_validates(self):
        t = StockTransfer("b01", "b02", "pcm500", 5)
        self.assertEqual((t.from_branch, t.to_branch, t.medicine_code), ("B01", "B02", "PCM500"))
        with self.assertRaises(ValidationError):
            StockTransfer("B01", "B01", "PCM500", 5)
        with self.assertRaises(InvalidQuantityError):
            StockTransfer("B01", "B02", "PCM500", 0)

    def test_category_property(self):
        self.assertEqual(OrdinaryMedicine("A", "A", 1, 0).category, "ORDINARY")
        self.assertEqual(NarcoticMedicine("N", "N", 1, 0).category, "NARCOTIC")


if __name__ == "__main__":
    unittest.main()
