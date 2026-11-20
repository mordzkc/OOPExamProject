"""Interface tests. They need a display, so they are skipped on a machine without one.
On Linux without a screen run:  xvfb-run -a python -m unittest tests.test_ui -v
"""
import tkinter as tk
import unittest
from unittest import mock

from pharmacy.ui.app import MainWindow
from tests.helpers import make_services


def display_available() -> bool:
    try:
        root = tk.Tk()
        root.destroy()
        return True
    except tk.TclError:
        return False


@unittest.skipUnless(display_available(), "no display available")
class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.svc = make_services()
        self.errors, self.infos = [], []
        patcher = mock.patch("pharmacy.ui.app.messagebox.showerror",
                             side_effect=lambda title, msg: self.errors.append((title, msg)))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.app = MainWindow(self.svc)
        self.addCleanup(self.app.destroy)
        self.med, self.stock, self.rx, self.low = self.app.frames

    def rows(self, tree):
        return [tree.item(i, "values") for i in tree.get_children()]

    # ---------------------------------------------------------- positive
    def test_startup_shows_seed_data(self):
        self.assertEqual(self.app.current_branch_id, "B01")
        self.assertEqual(len(self.rows(self.med.tree)), 6)
        self.assertEqual(len(self.rows(self.rx.tree)), 4)

    def test_register_medicine(self):
        self.med.code.set("tst100"); self.med.name.set("Test syrup")
        self.med.price.set("1,500"); self.med.reorder.set("12"); self.med.category.set("ORDINARY")
        self.med.on_register()
        self.assertEqual(self.errors, [])
        self.assertIn("TST100", [r[0] for r in self.rows(self.med.tree)])
        self.assertIn("registered", self.app.status_var.get())

    def test_receive_stock_updates_table(self):
        self.stock.medicine.set("PCM500 - Paracetamol 500mg"); self.stock.quantity.set("25")
        self.stock.on_receive()
        self.assertEqual(self.errors, [])
        row = [r for r in self.rows(self.stock.tree) if r[0] == "PCM500"][0]
        self.assertEqual(row[2], "225")

    def test_create_then_dispense(self):
        self.rx.patient.set("PT-0100")
        self.rx.medicine.set("PCM500 - Paracetamol 500mg"); self.rx.quantity.set("3")
        self.rx.on_add_line()
        self.rx.on_create()
        self.assertEqual(self.errors, [])
        self.rx.tree.selection_set("5")
        self.rx.on_dispense()
        self.assertEqual(self.errors, [])
        self.assertEqual(self.rx.tree.item("5", "values")[4], "dispensed")

    def test_low_stock_screen(self):
        self.assertEqual(len(self.rows(self.low.tree)), 4)
        self.assertIn("4 item(s)", self.low.summary.get())
        self.low.scope.set("Selected branch"); self.low.refresh()
        self.assertEqual(len(self.rows(self.low.tree)), 3)


    # ---------------------------------------------------------- rejections
    def test_duplicate_medicine_code(self):
        self.med.code.set("PCM500"); self.med.name.set("Again"); self.med.price.set("100")
        self.med.on_register()
        self.assertIn("already exists", self.errors[-1][1])

    def test_invalid_price_text_and_zero(self):
        self.med.code.set("Z1"); self.med.name.set("Z")
        for text, expect in (("abc", "must be a number"), ("0", "positive"), ("-5", "positive"),
                             ("nan", "positive"), ("", "required")):
            self.med.price.set(text)
            self.med.on_register()
            self.assertIn(expect, self.errors[-1][1], text)

    def test_invalid_stock_quantities(self):
        self.stock.medicine.set("PCM500 - Paracetamol 500mg")
        for text, expect in (("0", "above zero"), ("-3", "above zero"), ("ten", "whole number"),
                             ("2000", "Capacity")):
            self.stock.quantity.set(text)
            self.stock.on_receive()
            self.assertIn(expect, self.errors[-1][1], text)
        self.stock.medicine.set("")
        self.stock.quantity.set("5")
        self.stock.on_receive()
        self.assertIn("Medicine is required", self.errors[-1][1])

    def test_prescription_missing_information(self):
        self.rx.on_create()                                   # nothing entered
        self.assertIn("Patient id must look like", self.errors[-1][1])
        self.rx.patient.set("PT-0100")
        self.rx.on_create()                                   # patient but no lines
        self.assertIn("at least one line", self.errors[-1][1])
        self.rx.quantity.set("2")
        self.rx.on_add_line()                                 # no medicine chosen
        self.assertIn("Medicine is required", self.errors[-1][1])

    def test_dispense_needs_selection(self):
        self.rx.on_dispense()
        self.assertIn("Select a prescription", self.errors[-1][1])

    def test_oversell_message_and_no_change(self):
        self.rx.tree.selection_set("4")
        self.rx.on_dispense()
        self.assertIn("Only 35 in stock, 100 requested", self.errors[-1][1])
        self.assertEqual(self.rx.tree.item("4", "values")[4], "pending")

    def test_unauthorised_prescriber_message(self):
        self.rx.tree.selection_set("3")
        self.rx.on_dispense()
        self.assertIn("not authorised", self.errors[-1][1])

    def test_dispense_twice(self):
        self.rx.tree.selection_set("1")
        self.rx.on_dispense()
        self.rx.on_dispense()
        self.assertIn("already dispensed", self.errors[-1][1])


if __name__ == "__main__":
    unittest.main()
