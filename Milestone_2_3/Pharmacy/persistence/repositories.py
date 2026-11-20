import sqlite3

from ..domain.allowlist import PrescriberAllowList
from ..domain.branch import Branch
from ..domain.exceptions import (DuplicateCodeError, NotFoundError, InvalidStatusTransitionError)
from ..domain.medicine import medicine_from_row
from ..domain.prescription import Prescription, PrescriptionLine, PrescriptionStatus
from ..domain.stock import StockItem


class BranchRepository:
    def __init__(self, db):
        self._db = db

    def add(self, branch: Branch) -> None:
        try:
            self._db.conn.execute("INSERT INTO branches (branch_id, name, location) VALUES (?,?,?)",
                                  (branch.branch_id, branch.name, branch.location))
        except sqlite3.IntegrityError:
            raise DuplicateCodeError(f"Branch {branch.branch_id} already exists.") from None

    def get(self, branch_id: str) -> Branch:
        row = self._db.conn.execute("SELECT * FROM branches WHERE branch_id = ?",
                                    (str(branch_id).strip().upper(),)).fetchone()
        if row is None:
            raise NotFoundError(f"Branch {branch_id!r} does not exist.")
        return Branch(row["branch_id"], row["name"], row["location"])

    def list(self):
        rows = self._db.conn.execute("SELECT * FROM branches ORDER BY branch_id").fetchall()
        return [Branch(r["branch_id"], r["name"], r["location"]) for r in rows]


class MedicineRepository:
    def __init__(self, db):
        self._db = db

    def add(self, med) -> None:
        try:
            self._db.conn.execute(
                "INSERT INTO medicines (code, name, unit_price, reorder_level, category) VALUES (?,?,?,?,?)",
                (med.code, med.name, med.unit_price, med.reorder_level, med.CATEGORY))
        except sqlite3.IntegrityError:
            raise DuplicateCodeError(f"Medicine code {med.code} already exists.") from None

    def get(self, code: str):
        row = self._db.conn.execute("SELECT * FROM medicines WHERE code = ?",
                                    (str(code).strip().upper(),)).fetchone()
        if row is None:
            raise NotFoundError(f"Medicine {code!r} does not exist.")
        return medicine_from_row(row)

    def list(self):
        rows = self._db.conn.execute("SELECT * FROM medicines ORDER BY code").fetchall()
        return [medicine_from_row(r) for r in rows]


class StockRepository:
    def __init__(self, db):
        self._db = db

    def get(self, branch_id: str, medicine_code: str) -> StockItem:
        """Return the stock item, or an empty one (quantity 0) if none exists yet."""
        row = self._db.conn.execute(
            "SELECT * FROM stock WHERE branch_id = ? AND medicine_code = ?",
            (branch_id, medicine_code)).fetchone()
        if row is None:
            return StockItem(branch_id, medicine_code)
        return StockItem(row["branch_id"], row["medicine_code"], row["quantity"], row["max_capacity"])

    def save(self, item: StockItem) -> None:
        """Insert or update the row for this branch and medicine."""
        self._db.conn.execute(
            "INSERT INTO stock (branch_id, medicine_code, quantity, max_capacity) VALUES (?,?,?,?) "
            "ON CONFLICT(branch_id, medicine_code) DO UPDATE SET quantity = excluded.quantity",
            (item.branch_id, item.medicine_code, item.quantity, item.max_capacity))

    def list_for_branch(self, branch_id: str):
        rows = self._db.conn.execute(
            "SELECT * FROM stock WHERE branch_id = ? ORDER BY medicine_code", (branch_id,)).fetchall()
        return [StockItem(r["branch_id"], r["medicine_code"], r["quantity"], r["max_capacity"])
                for r in rows]

    def level_rows(self, branch_id: str):
        """Stock rows joined with medicine name and reorder level (for the stock screen)."""
        return self._db.conn.execute(
            "SELECT s.branch_id, s.medicine_code, m.name AS medicine_name, s.quantity, m.reorder_level "
            "FROM stock s JOIN medicines m ON m.code = s.medicine_code "
            "WHERE s.branch_id = ? ORDER BY s.medicine_code", (branch_id,)).fetchall()

    def low_stock_rows(self, branch_id=None):
        return self._db.conn.execute(
            "SELECT s.branch_id, s.medicine_code, s.quantity, m.reorder_level "
            "FROM stock s JOIN medicines m ON m.code = s.medicine_code "
            "WHERE s.quantity <= m.reorder_level AND (:branch IS NULL OR s.branch_id = :branch) "
            "ORDER BY s.branch_id, s.quantity", {"branch": branch_id}).fetchall()


class PrescriberRepository:
    def __init__(self, db):
        self._db = db

    def allow_list(self) -> PrescriberAllowList:
        rows = self._db.conn.execute(
            "SELECT prescriber_code FROM prescribers WHERE active = 1").fetchall()
        return PrescriberAllowList(r["prescriber_code"] for r in rows)


class PrescriptionRepository:
    def __init__(self, db):
        self._db = db

    def add(self, rx: Prescription) -> int:
        cur = self._db.conn.execute(
            "INSERT INTO prescriptions (patient_id, branch_id, prescriber_code, status) VALUES (?,?,?,?)",
            (rx.patient_id, rx.branch_id, rx.prescriber_code, rx.status.value))
        rx.assign_id(cur.lastrowid)
        for line in rx.lines:
            self._db.conn.execute(
                "INSERT INTO prescription_lines (prescription_id, medicine_code, quantity) VALUES (?,?,?)",
                (rx.id, line.medicine_code, line.quantity))
        return rx.id

    def get(self, rx_id: int) -> Prescription:
        row = self._db.conn.execute("SELECT * FROM prescriptions WHERE id = ?", (rx_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"Prescription {rx_id} does not exist.")
        lines = [PrescriptionLine(r["medicine_code"], r["quantity"]) for r in self._db.conn.execute(
            "SELECT * FROM prescription_lines WHERE prescription_id = ? ORDER BY id", (rx_id,))]
        return Prescription(row["patient_id"], row["branch_id"], row["prescriber_code"],
                            PrescriptionStatus(row["status"]), row["id"], lines)

    def list(self, status=None):
        sql, args = "SELECT id FROM prescriptions", ()
        if status is not None:
            sql, args = sql + " WHERE status = ?", (status.value,)
        ids = [r["id"] for r in self._db.conn.execute(sql + " ORDER BY id", args)]
        return [self.get(i) for i in ids]

    def _guarded_update(self, rx: Prescription, new_status: str, extra: str = "") -> None:
        cur = self._db.conn.execute(
            f"UPDATE prescriptions SET status = ?{extra} WHERE id = ? AND status = 'pending'",
            (new_status, rx.id))
        if cur.rowcount != 1:
            raise InvalidStatusTransitionError(
                f"Prescription {rx.id} is no longer pending, so it cannot become {new_status}.")

    def mark_dispensed(self, rx: Prescription) -> None:
        self._guarded_update(rx, "dispensed", ", dispensed_at = CURRENT_TIMESTAMP")

    def mark_cancelled(self, rx: Prescription) -> None:
        self._guarded_update(rx, "cancelled")
