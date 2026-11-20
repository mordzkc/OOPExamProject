-- Fictional sample data only. Safe to run more than once.
INSERT OR IGNORE INTO branches (branch_id, name, location) VALUES
    ('B01', 'Main Campus', 'Mukono'),
    ('B02', 'Satellite Clinic', 'Campus Gate');

INSERT OR IGNORE INTO medicines (code, name, unit_price, reorder_level, category) VALUES
    ('PCM500', 'Paracetamol 500mg', 300,  50, 'ORDINARY'),
    ('AMX250', 'Amoxicillin 250mg', 800,  40, 'ORDINARY'),
    ('ORS001', 'ORS sachet',        500,  30, 'ORDINARY'),
    ('DZP005', 'Diazepam 5mg',     1200,  20, 'CONTROLLED'),
    ('TRM050', 'Tramadol 50mg',    1500,  20, 'CONTROLLED'),
    ('MOR010', 'Morphine 10mg',    3000,  10, 'NARCOTIC');

INSERT OR IGNORE INTO stock (branch_id, medicine_code, quantity) VALUES
    ('B01', 'PCM500', 200), ('B01', 'AMX250', 35), ('B01', 'ORS001', 100),
    ('B01', 'DZP005', 15),  ('B01', 'MOR010', 4),
    ('B02', 'PCM500', 40),  ('B02', 'TRM050', 25);

INSERT OR IGNORE INTO prescribers (prescriber_code, name, active) VALUES
    ('DR-1001', 'Dr Test One', 1),
    ('DR-1002', 'Dr Test Two', 1);

-- Four demo prescriptions (ids 1 to 4). Fixed ids make this script safe to re-run.
INSERT OR IGNORE INTO prescriptions (id, patient_id, branch_id, prescriber_code) VALUES
    (1, 'PT-0001', 'B01', NULL),
    (2, 'PT-0002', 'B01', 'DR-1001'),
    (3, 'PT-0003', 'B01', 'DR-9999'),   -- DR-9999 is not on the allow-list
    (4, 'PT-0004', 'B01', NULL);

INSERT OR IGNORE INTO prescription_lines (id, prescription_id, medicine_code, quantity) VALUES
    (1, 1, 'PCM500', 10),
    (2, 1, 'ORS001', 5),
    (3, 2, 'DZP005', 5),
    (4, 3, 'DZP005', 5),
    (5, 4, 'AMX250', 100);              -- more than B01 holds, used to show the oversell rejection
