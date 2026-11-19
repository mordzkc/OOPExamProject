import unittest

from pharmacy.domain.exceptions import (InsufficientStockError, UnauthorisedPrescriberError,
                                        QuantityLimitError, InvalidStatusTransitionError,
                                        NotFoundError, ValidationError, CapacityExceededError)
from pharmacy.domain.lowstock import Severity
from pharmacy.domain.prescription import PrescriptionStatus
from tests.helpers import make_services, stock_qty


class Dispensing(unittest.TestCase):
    def setUp(self):
        self.svc = make_services()

    def test_t05_stock_is_per_branch(self):
        self.assertEqual(stock_qty(self.svc, "B01", "PCM500"), 200)
        self.assertEqual(stock_qty(self.svc, "B02", "PCM500"), 40)
        self.svc.stock.receive("B02", "PCM500", 10)
        self.assertEqual(stock_qty(self.svc, "B01", "PCM500"), 200)
        self.assertEqual(stock_qty(self.svc, "B02", "PCM500"), 50)

    def test_receive_creates_row_and_checks_capacity(self):
        self.assertEqual(self.svc.stock.receive("B02", "AMX250", 20), 20)
        with self.assertRaises(CapacityExceededError):
            self.svc.stock.receive("B02", "AMX250", 981)
        with self.assertRaises(NotFoundError):
            self.svc.stock.receive("B99", "AMX250", 1)

    def test_t07_create_multi_line_prescription(self):
        rx = self.svc.prescriptions.create("PT-0010", "B01", None,
                                           [("PCM500", 2), ("ORS001", 3)])
        got = self.svc.prescriptions.get(rx.id)
        self.assertEqual(len(got.lines), 2)
        self.assertIs(got.status, PrescriptionStatus.PENDING)
        with self.assertRaises(ValidationError):
            self.svc.prescriptions.create("BAD", "B01", None, [("PCM500", 1)])
        with self.assertRaises(ValidationError):
            self.svc.prescriptions.create("PT-0011", "B01", None, [])

    def test_t08_dispense_ordinary(self):
        rx = self.svc.dispensing.dispense(1)          # PCM500 x10, ORS001 x5 at B01
        self.assertIs(rx.status, PrescriptionStatus.DISPENSED)
        self.assertEqual(stock_qty(self.svc, "B01", "PCM500"), 190)
        self.assertEqual(stock_qty(self.svc, "B01", "ORS001"), 95)
        self.assertIs(self.svc.prescriptions.get(1).status, PrescriptionStatus.DISPENSED)

    def test_t09_oversell_rejected_and_rolled_back(self):
        before = stock_qty(self.svc, "B01", "AMX250")
        with self.assertRaises(InsufficientStockError):
            self.svc.dispensing.dispense(4)           # AMX250 x100, only 35 held
        self.assertEqual(stock_qty(self.svc, "B01", "AMX250"), before)
        self.assertIs(self.svc.prescriptions.get(4).status, PrescriptionStatus.PENDING)

    def test_t10_unauthorised_prescriber(self):
        with self.assertRaises(UnauthorisedPrescriberError):
            self.svc.dispensing.dispense(3)           # DR-9999 is not on the allow-list
        self.assertEqual(stock_qty(self.svc, "B01", "DZP005"), 15)
        self.assertIs(self.svc.prescriptions.get(3).status, PrescriptionStatus.PENDING)

    def test_controlled_without_prescriber_rejected(self):
        rx = self.svc.prescriptions.create("PT-0012", "B01", None, [("DZP005", 1)])
        with self.assertRaises(UnauthorisedPrescriberError):
            self.svc.dispensing.dispense(rx.id)

    def test_t11_authorised_prescriber(self):
        rx = self.svc.dispensing.dispense(2)          # DZP005 x5 with DR-1001
        self.assertIs(rx.status, PrescriptionStatus.DISPENSED)
        self.assertEqual(stock_qty(self.svc, "B01", "DZP005"), 10)

    def test_t12_line_caps(self):
        rx1 = self.svc.prescriptions.create("PT-0013", "B01", "DR-1001", [("DZP005", 31)])
        with self.assertRaises(QuantityLimitError):
            self.svc.dispensing.dispense(rx1.id)
        rx2 = self.svc.prescriptions.create("PT-0014", "B01", "DR-1001", [("MOR010", 11)])
        with self.assertRaises(QuantityLimitError):
            self.svc.dispensing.dispense(rx2.id)

    def test_t13_cannot_dispense_twice(self):
        self.svc.dispensing.dispense(1)
        with self.assertRaises(InvalidStatusTransitionError):
            self.svc.dispensing.dispense(1)
        self.assertEqual(stock_qty(self.svc, "B01", "PCM500"), 190)   # no second reduction

    def test_t14_cancel_then_cannot_dispense(self):
        self.svc.prescriptions.cancel(1)
        self.assertIs(self.svc.prescriptions.get(1).status, PrescriptionStatus.CANCELLED)
        with self.assertRaises(InvalidStatusTransitionError):
            self.svc.dispensing.dispense(1)
        with self.assertRaises(InvalidStatusTransitionError):
            self.svc.prescriptions.cancel(1)

    def test_t17_second_line_fails_first_line_restored(self):
        rx = self.svc.prescriptions.create("PT-0015", "B01", None,
                                           [("PCM500", 10), ("AMX250", 100)])
        with self.assertRaises(InsufficientStockError):
            self.svc.dispensing.dispense(rx.id)
        self.assertEqual(stock_qty(self.svc, "B01", "PCM500"), 200)   # line 1 undone
        self.assertIs(self.svc.prescriptions.get(rx.id).status, PrescriptionStatus.PENDING)

    def test_same_medicine_on_two_lines_cannot_oversell(self):
        rx = self.svc.prescriptions.create("PT-0016", "B01", None,
                                           [("AMX250", 20), ("AMX250", 20)])   # 40 > 35
        with self.assertRaises(InsufficientStockError):
            self.svc.dispensing.dispense(rx.id)
        self.assertEqual(stock_qty(self.svc, "B01", "AMX250"), 35)

    def test_t15_low_stock_list(self):
        items = {(i.branch_id, i.medicine_code): i for i in self.svc.stock.low_stock()}
        self.assertEqual(set(items), {("B01", "AMX250"), ("B01", "DZP005"),
                                      ("B01", "MOR010"), ("B02", "PCM500")})
        self.assertIs(items[("B01", "MOR010")].severity, Severity.CRITICAL)
        self.assertEqual(items[("B01", "MOR010")].suggested_reorder, 16)
        self.assertIs(items[("B01", "DZP005")].severity, Severity.LOW)
        only_b02 = self.svc.stock.low_stock("B02")
        self.assertEqual([(i.branch_id, i.medicine_code) for i in only_b02], [("B02", "PCM500")])


if __name__ == "__main__":
    unittest.main()
