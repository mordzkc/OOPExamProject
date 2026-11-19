import unittest

from pharmacy.domain.exceptions import (CapacityExceededError, InsufficientStockError,
                                        InvalidQuantityError, ValidationError,
                                        InvalidStatusTransitionError)
from pharmacy.domain.lowstock import Severity, classify, suggested_reorder
from pharmacy.domain.prescription import Prescription, PrescriptionStatus
from pharmacy.domain.stock import StockItem


class StockItemRules(unittest.TestCase):
    def test_add_and_remove(self):
        s = StockItem("B01", "PCM500", 10, 100)
        s.add(5)
        s.remove(12)
        self.assertEqual(s.quantity, 3)

    def test_never_negative(self):
        s = StockItem("B01", "PCM500", 3, 100)
        with self.assertRaises(InsufficientStockError):
            s.remove(4)
        self.assertEqual(s.quantity, 3)

    def test_t06_capacity(self):
        s = StockItem("B01", "PCM500", 95, 100)
        with self.assertRaises(CapacityExceededError):
            s.add(6)
        self.assertEqual(s.quantity, 95)

    def test_bad_quantities(self):
        s = StockItem("B01", "PCM500", 5, 100)
        for bad in (0, -1, 1.5, "3", True):
            with self.assertRaises(InvalidQuantityError):
                s.add(bad)


class PrescriptionRules(unittest.TestCase):
    def make(self):
        rx = Prescription("PT-0001", "b01", "dr-1001")
        rx.add_line("pcm500", 2)
        return rx

    def test_patient_id_format(self):
        for bad in ("0001", "PT-1", "PT-00012", "pt-0001", ""):
            with self.assertRaises(ValidationError, msg=bad):
                Prescription(bad, "B01")

    def test_normalised_fields(self):
        rx = self.make()
        self.assertEqual(rx.branch_id, "B01")
        self.assertEqual(rx.prescriber_code, "DR-1001")
        self.assertEqual(rx.lines[0].medicine_code, "PCM500")

    def test_status_machine(self):
        rx = self.make()
        rx.mark_dispensed()
        self.assertIs(rx.status, PrescriptionStatus.DISPENSED)
        with self.assertRaises(InvalidStatusTransitionError):
            rx.cancel()
        with self.assertRaises(InvalidStatusTransitionError):
            rx.ensure_dispensable()

    def test_lines_tuple_is_read_only(self):
        rx = self.make()
        self.assertIsInstance(rx.lines, tuple)

    def test_empty_prescription_not_dispensable(self):
        with self.assertRaises(ValidationError):
            Prescription("PT-0001", "B01").ensure_dispensable()


class LowStockRules(unittest.TestCase):
    def test_worked_example(self):
        cases = {51: (None, 0), 50: (Severity.LOW, 50), 26: (Severity.LOW, 74),
                 25: (Severity.CRITICAL, 75), 0: (Severity.CRITICAL, 100)}
        for qty, (sev, sug) in cases.items():
            self.assertEqual(classify(qty, 50), sev, qty)
            if sev:
                self.assertEqual(suggested_reorder(qty, 50), sug, qty)


if __name__ == "__main__":
    unittest.main()
