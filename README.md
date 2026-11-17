# Multi-Branch Campus Pharmacy Inventory, Dispensing & Reporting System

**Course:** CSC2105 – Object-Oriented Programming Using Python  
**Institution:** Uganda Christian University  
**Program:** Bachelor of Science in Data Science  
**Academic Year:** Advent 2026

A desktop pharmacy management system designed for multi-branch campus health services. The system supports medicine registration, per-branch stock control, multi-line prescriptions, atomic dispensing, controlled-medicine validation, and low-stock monitoring.

---

## Key Features

- Multi-branch stock management (same medicine can have different quantities per branch)
- Full prescription lifecycle (Pending → Dispensed / Cancelled)
- Atomic dispensing with transaction rollback on failure
- Controlled medicine allow-list enforcement
- Low-stock detection and reporting
- Clean object-oriented domain model with inheritance and polymorphism
- Persistent storage using SQLite
- Desktop GUI built with tkinter

---

## Unique Design Concepts

This project goes beyond the minimum requirements through several deliberate design decisions:

### 1. Rich Inheritance Hierarchy
- `Medicine` (abstract base class)
- `OrdinaryMedicine`
- `ControlledMedicine`
- Extensible for future categories (e.g., High-Alert or Narcotic medicines)

### 2. Polymorphism in Dispensing Logic
Dispensing behaviour differs by medicine type:
- Ordinary medicines → standard stock validation and deduction
- Controlled medicines → allow-list verification + additional quantity constraints

### 3. Strong Domain Invariants
Explicit rules enforced in the domain layer, including:
- Unit price must always be positive
- Stock quantity can never become negative
- Controlled medicines cannot be dispensed without an authorised prescriber
- A dispensed or cancelled prescription cannot be dispensed again
- Additional business rules (e.g., maximum quantity limits for controlled items)

### 4. Multi-Branch Transfer Support (Designed)
Stock transfers between branches are modelled as a first-class concept, enabling future implementation of inter-branch movements with full auditability.

### 5. Enhanced Low-Stock Intelligence
- Distinguishes between items at reorder level and critically low stock
- Supports branch-specific and cross-branch low-stock views
- Provides foundation for suggested reorder quantities

### 6. Clean Layered Architecture
Clear separation of concerns:
- **Domain Layer** – Pure OOP model with business rules and invariants
- **Persistence Layer** – SQLite repositories
- **Presentation Layer** – tkinter GUI

### 7. Privacy & Audit Awareness
- Only fictional patient identifiers are used
- Simulated prescriber allow-list
- Design includes hooks for basic audit logging of dispensing actions

---

## Technology Stack

- **Language:** Python 3
- **GUI:** tkinter (standard library)
- **Database:** SQLite (standard library)
- **Paradigm:** Object-Oriented Programming (inheritance, encapsulation, polymorphism)

> No external packages are required unless explicitly approved.

---

## Project Structure

```text
pharmacy-system/
├── domain/                 # Core business classes
├── persistence/            # SQLite repositories & schema
├── gui/                    # tkinter interface
├── data/                   # Sample data & database (ignored by git)
├── tests/                  # Test scripts / checklist
├── docs/                   # Design documents & diagrams
├── main.py                 # Application entry point
├── requirements.txt
├── .gitignore
└── README.md
