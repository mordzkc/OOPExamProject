"""Start the Campus Pharmacy desktop application: python main.py"""
from pharmacy.bootstrap import build_services
from pharmacy.config import DB_PATH
from pharmacy.persistence.database import Database
from pharmacy.ui.app import MainWindow


def main() -> None:
    db = Database(DB_PATH)
    db.create_schema()                      # safe to repeat: tables are created only if missing
    app = MainWindow(build_services(db))
    if not app.branch_box["values"]:
        app.set_status("Database is empty. Run: python -m pharmacy.persistence.init_db --seed", error=True)
    app.mainloop()
    db.close()


if __name__ == "__main__":
    main()
