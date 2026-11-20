"""Console demo for the Milestone Two live check. Run after: python -m pharmacy.persistence.init_db --reset --seed"""
from pharmacy.bootstrap import build_services
from pharmacy.config import DB_PATH
from pharmacy.domain.exceptions import PharmacyError
from pharmacy.persistence.database import Database


def attempt(label, action):
    try:
        action()
        print(f"[OK]       {label}")
    except PharmacyError as err:
        print(f"[REJECTED] {label}: {err}")


db = Database(DB_PATH)
svc = build_services(db)
stock = svc.repos.stock

print("--- registration rules")
attempt("register medicine with price 0", lambda: svc.medicines.register("BAD1", "Bad", 0, 5))
attempt("register duplicate code PCM500", lambda: svc.medicines.register("PCM500", "Dup", 100, 5))
print("--- dispensing")
attempt("dispense #1 (ordinary, B01)", lambda: svc.dispensing.dispense(1))
attempt("dispense #1 again", lambda: svc.dispensing.dispense(1))
attempt("dispense #2 (controlled, DR-1001)", lambda: svc.dispensing.dispense(2))
attempt("dispense #3 (controlled, DR-9999)", lambda: svc.dispensing.dispense(3))
attempt("dispense #4 (oversell AMX250 x100)", lambda: svc.dispensing.dispense(4))
print("--- stock after the run (B01)")
for item in stock.list_for_branch("B01"):
    print(f"    {item.medicine_code:7} {item.quantity:4}")
print("--- low stock (all branches)")
for i in svc.stock.low_stock():
    print(f"    {i.branch_id} {i.medicine_code:7} qty={i.quantity:3} reorder={i.reorder_level:3} "
          f"{i.severity.value:8} suggest +{i.suggested_reorder}")
print("--- prescription statuses")
for rx in svc.prescriptions.list():
    print(f"    #{rx.id} {rx.patient_id} {rx.status.value}")
db.close()
