from pharmacy.bootstrap import build_services
from pharmacy.persistence.database import Database


def make_services(seed=True):
    """In-memory database with schema and (optionally) the fictional seed data."""
    db = Database(":memory:")
    db.create_schema()
    if seed:
        db.load_seed()
    return build_services(db)


def stock_qty(svc, branch, code):
    return svc.repos.stock.get(branch, code).quantity
