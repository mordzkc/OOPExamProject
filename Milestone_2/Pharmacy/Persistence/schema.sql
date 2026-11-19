PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS branches (
    branch_id TEXT PRIMARY KEY,
    name      TEXT NOT NULL,
    location  TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS medicines (
    code          TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    unit_price    REAL NOT NULL CHECK (unit_price > 0),
    reorder_level INTEGER NOT NULL CHECK (reorder_level >= 0),
    category      TEXT NOT NULL CHECK (category IN ('ORDINARY','CONTROLLED','NARCOTIC'))
);

CREATE TABLE IF NOT EXISTS stock (
    branch_id     TEXT NOT NULL REFERENCES branches(branch_id),
    medicine_code TEXT NOT NULL REFERENCES medicines(code),
    quantity      INTEGER NOT NULL CHECK (quantity >= 0),
    max_capacity  INTEGER NOT NULL DEFAULT 1000 CHECK (max_capacity > 0),
    CHECK (quantity <= max_capacity),
    PRIMARY KEY (branch_id, medicine_code)
);

CREATE TABLE IF NOT EXISTS prescribers (
    prescriber_code TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE TABLE IF NOT EXISTS prescriptions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id      TEXT NOT NULL,
    branch_id       TEXT NOT NULL REFERENCES branches(branch_id),
    prescriber_code TEXT,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','dispensed','cancelled')),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dispensed_at    TEXT
);

CREATE TABLE IF NOT EXISTS prescription_lines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL REFERENCES prescriptions(id) ON DELETE CASCADE,
    medicine_code   TEXT NOT NULL REFERENCES medicines(code),
    quantity        INTEGER NOT NULL CHECK (quantity > 0)
);
