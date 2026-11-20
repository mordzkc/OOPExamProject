from types import SimpleNamespace

from .domain.services import (BranchService, MedicineService, StockService,
                              PrescriptionService, DispensingService)
from .persistence.database import Database
from .persistence.repositories import (BranchRepository, MedicineRepository, StockRepository,
                                       PrescriberRepository, PrescriptionRepository)


def build_services(db: Database) -> SimpleNamespace:
    """Wire repositories and services. The tkinter app (M3) calls only this."""
    branches, medicines = BranchRepository(db), MedicineRepository(db)
    stock, prescribers = StockRepository(db), PrescriberRepository(db)
    prescriptions = PrescriptionRepository(db)
    return SimpleNamespace(
        db=db,
        branches=BranchService(db, branches),
        medicines=MedicineService(db, medicines),
        stock=StockService(db, branches, medicines, stock),
        prescriptions=PrescriptionService(db, branches, medicines, prescriptions),
        dispensing=DispensingService(db, medicines, stock, prescriptions, prescribers),
        repos=SimpleNamespace(branches=branches, medicines=medicines, stock=stock,
                              prescriptions=prescriptions, prescribers=prescribers),
    )
