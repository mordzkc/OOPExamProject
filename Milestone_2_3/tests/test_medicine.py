import unittest

from pharmacy.domain.allowlist import PrescriberAllowList
from pharmacy.domain.exceptions import (InvalidPriceError, ValidationError, DuplicateCodeError,
                                        UnauthorisedPrescriberError, QuantityLimitError)
from pharmacy.domain.medicine import (Medicine, OrdinaryMedicine, ControlledMedicine,
                                      NarcoticMedicine)
from tests.helpers import make_services


class MedicineRules(unittest.TestCase):
    def test_t01_valid_medicine(self):
        m = OrdinaryMedicine("pcm500", "Paracetamol", 300, 50)
        self.assertEqual(m.code, "PCM500")
        self.assertEqual(m.unit_price, 300.0)

    def test_t02_invalid_price_rejected(self):
        for bad in (0, -5, "abc", None, True):
            with self.assertRaises(InvalidPriceError, msg=repr(bad)):
                OrdinaryMedicine("X1", "X", bad, 10)

    def test_price_setter_also_validates(self):
        m = OrdinaryMedicine("X1", "X", 100, 10)
        with self.assertRaises(InvalidPriceError):
            m.unit_price = -1
        self.assertEqual(m.unit_price, 100.0)

    def test_t04_negative_reorder_rejected(self):
        with self.assertRaises(ValidationError):
            OrdinaryMedicine("X1", "X", 100, -1)

    def test_abstract_base_cannot_be_created(self):
        with self.assertRaises(TypeError):
            Medicine("X1", "X", 100, 1)

    def test_t03_duplicate_code_rejected(self):
        svc = make_services(seed=False)
        svc.medicines.register("A1", "Alpha", 100, 5)
        with self.assertRaises(DuplicateCodeError):
            svc.medicines.register("a1", "Alpha again", 200, 5)

    def test_polymorphic_validate_dispense(self):
        allow = PrescriberAllowList(["DR-1001"])
        ordinary = OrdinaryMedicine("O1", "Ord", 10, 1)
        controlled = ControlledMedicine("C1", "Ctl", 10, 1)
        narcotic = NarcoticMedicine("N1", "Nar", 10, 1)
        ordinary.validate_dispense(500, None, allow)             # no allow-list, no cap
        with self.assertRaises(UnauthorisedPrescriberError):
            controlled.validate_dispense(5, "DR-9999", allow)
        with self.assertRaises(UnauthorisedPrescriberError):
            controlled.validate_dispense(5, "", allow)           # empty string is not enough
        controlled.validate_dispense(30, "DR-1001", allow)
        with self.assertRaises(QuantityLimitError):
            controlled.validate_dispense(31, "DR-1001", allow)
        narcotic.validate_dispense(10, "DR-1001", allow)
        with self.assertRaises(QuantityLimitError):
            narcotic.validate_dispense(11, "DR-1001", allow)
        self.assertTrue(narcotic.is_high_alert)
        self.assertIsInstance(narcotic, ControlledMedicine)


if __name__ == "__main__":
    unittest.main()
