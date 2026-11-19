import os
import tempfile
import unittest

from pharmacy.bootstrap import build_services
from pharmacy.persistence.database import Database


class Persistence(unittest.TestCase):
    def test_t16_data_survives_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "test.db")
            db = Database(path)
            db.create_schema()
            db.load_seed()
            svc = build_services(db)
            svc.medicines.register("NEW001", "Test medicine", 250, 5)
            svc.stock.receive("B01", "NEW001", 7)
            svc.dispensing.dispense(1)
            db.close()                                    # simulate closing the application

            db2 = Database(path)                          # simulate starting it again
            svc2 = build_services(db2)
            self.assertEqual(svc2.repos.medicines.get("NEW001").unit_price, 250.0)
            self.assertEqual(svc2.repos.stock.get("B01", "NEW001").quantity, 7)
            self.assertEqual(svc2.repos.stock.get("B01", "PCM500").quantity, 190)
            self.assertEqual(svc2.prescriptions.get(1).status.value, "dispensed")
            db2.close()

    def test_seed_is_safe_to_run_twice(self):
        db = Database(":memory:")
        db.create_schema()
        db.load_seed()
        db.load_seed()
        count = db.conn.execute("SELECT COUNT(*) FROM prescription_lines").fetchone()[0]
        self.assertEqual(count, 5)

    def test_database_constraints_are_a_backstop(self):
        import sqlite3
        db = Database(":memory:")
        db.create_schema()
        with self.assertRaises(sqlite3.IntegrityError):
            db.conn.execute("INSERT INTO medicines VALUES ('Z1','Z',0,1,'ORDINARY')")
        with self.assertRaises(sqlite3.IntegrityError):
            db.conn.execute("INSERT INTO medicines VALUES ('Z1','Z',5,-1,'ORDINARY')")
        db.load_seed()
        with self.assertRaises(sqlite3.IntegrityError):
            db.conn.execute("UPDATE stock SET quantity = -1 WHERE branch_id='B01' AND medicine_code='PCM500'")


if __name__ == "__main__":
    unittest.main()
