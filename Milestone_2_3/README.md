# Campus Pharmacy System (CSC2105), Milestone Two reference code

Python 3.10+ and the standard library only. Run every command from this folder.

    python -m pharmacy.persistence.init_db --reset --seed   # create the database and load fictional data
    python demo_m2.py                                       # console demo of rules and atomic dispensing
    python -m unittest discover -s tests -t .               # run all tests

Layers: pharmacy/domain (entities, rules, services), pharmacy/persistence (SQLite), tests/.
The tkinter interface is added in Milestone Three and calls only pharmacy.bootstrap.build_services().
All patient, prescriber and staff data is fictional.
