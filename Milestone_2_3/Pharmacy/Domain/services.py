from .branch import Branch
from .exceptions import PharmacyError, ValidationError
from .lowstock import LowStockItem, classify, suggested_reorder
from .medicine import medicine_class_for
from .prescription import Prescription


class BranchService:
    def __init__(self, db, branches):
        self._db, self._branches = db, branches

    def register(self, branch_id, name, location="") -> Branch:
        branch = Branch(branch_id, name, location)
        with self._db.transaction():
            self._branches.add(branch)
        return branch


class MedicineService:
    def __init__(self, db, medicines):
        self._db, self._medicines = db, medicines

    def register(self, code, name, unit_price, reorder_level, category="ORDINARY"):
        cls = medicine_class_for(category)
        med = cls(code, name, unit_price, reorder_level)   # validation happens in the entity
        with self._db.transaction():
            self._medicines.add(med)                       # uniqueness enforced by the repository
        return med


class StockService:
    def __init__(self, db, branches, medicines, stock):
        self._db, self._branches, self._medicines, self._stock = db, branches, medicines, stock

    def receive(self, branch_id, medicine_code, quantity) -> int:
        with self._db.transaction():
            branch = self._branches.get(branch_id)
            med = self._medicines.get(medicine_code)
            item = self._stock.get(branch.branch_id, med.code)
            item.add(quantity)
            self._stock.save(item)
        return item.quantity

    def low_stock(self, branch_id=None):
        result = []
        for r in self._stock.low_stock_rows(branch_id):
            sev = classify(r["quantity"], r["reorder_level"])
            result.append(LowStockItem(r["branch_id"], r["medicine_code"], r["quantity"],
                                       r["reorder_level"], sev,
                                       suggested_reorder(r["quantity"], r["reorder_level"])))
        return result


class PrescriptionService:
    def __init__(self, db, branches, medicines, prescriptions):
        self._db, self._branches = db, branches
        self._medicines, self._prescriptions = medicines, prescriptions

    def create(self, patient_id, branch_id, prescriber_code, lines) -> Prescription:
        """lines is a list of (medicine_code, quantity). Stock is NOT checked here."""
        if not lines:
            raise ValidationError("A prescription needs at least one line.")
        with self._db.transaction():
            branch = self._branches.get(branch_id)
            rx = Prescription(patient_id, branch.branch_id, prescriber_code)
            for code, qty in lines:
                rx.add_line(self._medicines.get(code).code, qty)
            self._prescriptions.add(rx)
        return rx

    def cancel(self, rx_id) -> None:
        with self._db.transaction():
            rx = self._prescriptions.get(rx_id)
            rx.cancel()
            self._prescriptions.mark_cancelled(rx)

    def get(self, rx_id) -> Prescription:
        return self._prescriptions.get(rx_id)

    def list(self, status=None):
        return self._prescriptions.list(status)


class DispensingService:
    def __init__(self, db, medicines, stock, prescriptions, prescribers):
        self._db, self._medicines, self._stock = db, medicines, stock
        self._prescriptions, self._prescribers = prescriptions, prescribers

    def dispense(self, rx_id) -> Prescription:
        """All-or-nothing: any PharmacyError raised inside rolls the whole transaction back."""
        with self._db.transaction():
            rx = self._prescriptions.get(rx_id)
            rx.ensure_dispensable()
            allow_list = self._prescribers.allow_list()
            for line in rx.lines:
                med = self._medicines.get(line.medicine_code)
                med.validate_dispense(line.quantity, rx.prescriber_code, allow_list)  # polymorphic
                item = self._stock.get(rx.branch_id, line.medicine_code)              # fresh read
                item.remove(line.quantity)
                self._stock.save(item)
            rx.mark_dispensed()
            self._prescriptions.mark_dispensed(rx)
        return rx
