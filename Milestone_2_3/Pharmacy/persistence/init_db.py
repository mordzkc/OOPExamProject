"""Create the database. Usage:
    python -m pharmacy.persistence.init_db            create tables only
    python -m pharmacy.persistence.init_db --seed     create tables and load fictional sample data
    python -m pharmacy.persistence.init_db --reset    delete the file first (fresh start)
"""
import argparse

from ..config import DB_PATH
from .database import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the pharmacy SQLite database.")
    parser.add_argument("--seed", action="store_true", help="load fictional sample data")
    parser.add_argument("--reset", action="store_true", help="delete the existing database first")
    args = parser.parse_args()
    if args.reset and DB_PATH.exists():
        DB_PATH.unlink()
    db = Database(DB_PATH)
    db.create_schema()
    if args.seed:
        db.load_seed()
    db.close()
    print(f"Database ready at {DB_PATH}" + (" (seeded)" if args.seed else ""))


if __name__ == "__main__":
    main()
