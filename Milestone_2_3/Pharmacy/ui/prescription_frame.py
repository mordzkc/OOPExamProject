"""Screen S-04: build a prescription, then dispense or cancel it."""
import tkinter as tk
from tkinter import ttk

from ..domain.exceptions import ValidationError
from ..domain.prescription import PrescriptionStatus
from .validators import code_from_choice, parse_whole_number


class PrescriptionFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.pending_lines = []                      # [(medicine_code, quantity)] not yet saved
        self.patient, self.prescriber = tk.StringVar(), tk.StringVar()
        self.medicine, self.quantity = tk.StringVar(), tk.StringVar(value="1")
        self.filter = tk.StringVar(value="all")
        self._build_form()
        self._build_list()

    # ------------------------------------------------------------ layout
    def _build_form(self):
        form = ttk.LabelFrame(self, text="New prescription (at the selected branch)", padding=10)
        form.pack(fill="x")
        ttk.Label(form, text="Patient id (PT-0001)").grid(row=0, column=0, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.patient, width=14).grid(row=1, column=0, padx=4)
        ttk.Label(form, text="Prescriber code").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.prescriber, width=14).grid(row=1, column=1, padx=4)
        ttk.Label(form, text="Medicine").grid(row=0, column=2, sticky="w", padx=4)
        self.medicine_box = ttk.Combobox(form, textvariable=self.medicine, state="readonly", width=32)
        self.medicine_box.grid(row=1, column=2, padx=4)
        ttk.Label(form, text="Qty").grid(row=0, column=3, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.quantity, width=6).grid(row=1, column=3, padx=4)
        ttk.Button(form, text="Add line", command=self.on_add_line).grid(row=1, column=4, padx=4)

        self.line_tree = ttk.Treeview(form, columns=("code", "qty"), show="headings", height=3)
        self.line_tree.heading("code", text="Line medicine")
        self.line_tree.heading("qty", text="Quantity")
        self.line_tree.column("code", width=200)
        self.line_tree.column("qty", width=80)
        self.line_tree.grid(row=2, column=0, columnspan=3, sticky="we", padx=4, pady=(8, 0))
        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=3, columnspan=2, sticky="e", pady=(8, 0))
        ttk.Button(buttons, text="Remove line", command=self.on_remove_line).pack(side="left", padx=4)
        ttk.Button(buttons, text="Create prescription", style="Accent.TButton",
                   command=self.on_create).pack(side="left", padx=4)

    def _build_list(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(12, 4))
        ttk.Label(top, text="Prescriptions", font=("Helvetica", 11, "bold")).pack(side="left")
        box = ttk.Combobox(top, textvariable=self.filter, values=("all", "pending", "dispensed", "cancelled"),
                           state="readonly", width=12)
        box.pack(side="left", padx=10)
        box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Button(top, text="Cancel selected", command=self.on_cancel).pack(side="right", padx=4)
        ttk.Button(top, text="Dispense selected", style="Accent.TButton",
                   command=self.on_dispense).pack(side="right", padx=4)

        cols = ("id", "patient", "branch", "prescriber", "status", "lines")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=9)
        for col, text, width in (("id", "ID", 50), ("patient", "Patient", 90), ("branch", "Branch", 70),
                                 ("prescriber", "Prescriber", 90), ("status", "Status", 90),
                                 ("lines", "Lines", 420)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.tag_configure("dispensed", foreground="#1b5e20")
        self.tree.tag_configure("cancelled", foreground="#777777")
        self.tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------ line editor
    def on_add_line(self):
        def action():
            code = code_from_choice(self.medicine.get(), "Medicine")
            qty = parse_whole_number(self.quantity.get(), "Line quantity")
            if qty <= 0:
                raise ValidationError("Line quantity must be above zero.")
            self.pending_lines.append((code, qty))
            return f"Added {qty} x {code}. {len(self.pending_lines)} line(s) so far."
        if self.app.run(action, "Line rejected"):
            self._show_lines()

    def on_remove_line(self):
        selected = self.line_tree.selection()
        if selected:
            del self.pending_lines[self.line_tree.index(selected[0])]
            self._show_lines()

    def _show_lines(self):
        self.line_tree.delete(*self.line_tree.get_children())
        for code, qty in self.pending_lines:
            self.line_tree.insert("", "end", values=(code, qty))

    # ------------------------------------------------------------ create, dispense, cancel
    def on_create(self):
        def action():
            rx = self.app.svc.prescriptions.create(           # stock is NOT checked here, by design
                self.patient.get(), self.app.current_branch_id, self.prescriber.get(),
                list(self.pending_lines))
            return f"Prescription {rx.id} created for {rx.patient_id} (pending)."
        if self.app.run(action, "Prescription rejected"):
            self.patient.set("")
            self.prescriber.set("")
            self.pending_lines.clear()
            self._show_lines()
            self.app.refresh_all()

    def _selected_id(self) -> int:
        selected = self.tree.selection()
        if not selected:
            raise ValidationError("Select a prescription in the list first.")
        return int(self.tree.item(selected[0], "values")[0])

    def on_dispense(self):
        def action():
            rx_id = self._selected_id()
            self.app.svc.dispensing.dispense(rx_id)           # atomic: all lines or nothing
            return f"Prescription {rx_id} dispensed. Stock updated."
        if self.app.run(action, "Dispense rejected"):
            self.app.refresh_all()

    def on_cancel(self):
        def action():
            rx_id = self._selected_id()
            self.app.svc.prescriptions.cancel(rx_id)
            return f"Prescription {rx_id} cancelled."
        if self.app.run(action, "Cancel rejected"):
            self.app.refresh_all()

    # ------------------------------------------------------------ refresh
    def refresh(self):
        meds = self.app.svc.repos.medicines.list()
        self.medicine_box["values"] = [f"{m.code} - {m.name}" for m in meds]
        previous = self.tree.selection()                   # keep the user's selection across refreshes
        self.tree.delete(*self.tree.get_children())
        wanted = None if self.filter.get() == "all" else PrescriptionStatus(self.filter.get())
        for rx in self.app.svc.prescriptions.list(wanted):
            lines = ", ".join(f"{l.medicine_code} x{l.quantity}" for l in rx.lines)
            self.tree.insert("", "end", iid=str(rx.id), tags=(rx.status.value,),
                             values=(rx.id, rx.patient_id, rx.branch_id, rx.prescriber_code or "-",
                                     rx.status.value, lines))
        for iid in previous:
            if self.tree.exists(iid):
                self.tree.selection_set(iid)
