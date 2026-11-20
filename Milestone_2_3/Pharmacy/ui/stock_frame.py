"""Screen S-03: receive stock at the selected branch and view current levels."""
import tkinter as tk
from tkinter import ttk

from .validators import code_from_choice, parse_whole_number


class StockFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.medicine, self.quantity = tk.StringVar(), tk.StringVar(value="10")

        form = ttk.LabelFrame(self, text="Receive stock at the selected branch", padding=10)
        form.pack(fill="x")
        ttk.Label(form, text="Medicine").grid(row=0, column=0, sticky="w", padx=4)
        self.medicine_box = ttk.Combobox(form, textvariable=self.medicine, state="readonly", width=40)
        self.medicine_box.grid(row=1, column=0, padx=4, pady=(2, 0))
        ttk.Label(form, text="Quantity received").grid(row=0, column=1, sticky="w", padx=4)
        ttk.Entry(form, textvariable=self.quantity, width=10).grid(row=1, column=1, padx=4, pady=(2, 0))
        ttk.Button(form, text="Receive stock", style="Accent.TButton",
                   command=self.on_receive).grid(row=1, column=2, padx=(14, 4))

        self.tree = ttk.Treeview(self, columns=("code", "name", "qty", "reorder", "level"),
                                 show="headings", height=14)
        for col, text, width in (("code", "Code", 90), ("name", "Medicine", 260), ("qty", "In stock", 90),
                                 ("reorder", "Reorder level", 110), ("level", "Status", 100)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.tag_configure("CRITICAL", background="#fde0e0", foreground="#8e0000")
        self.tree.tag_configure("LOW", background="#fff4d6", foreground="#7a5200")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))

    def on_receive(self):
        def action():
            branch = self.app.current_branch_id
            code = code_from_choice(self.medicine.get(), "Medicine")
            qty = parse_whole_number(self.quantity.get(), "Quantity received")
            total = self.app.svc.stock.receive(branch, code, qty)       # domain rules + one transaction
            return f"Received {qty} x {code} at {branch}. Now holding {total}."
        if self.app.run(action, "Stock receipt rejected"):
            self.app.refresh_all()

    def refresh(self):
        meds = self.app.svc.repos.medicines.list()
        self.medicine_box["values"] = [f"{m.code} - {m.name}" for m in meds]
        self.tree.delete(*self.tree.get_children())
        if not self.app.branch_var.get():
            return
        for lv in self.app.svc.stock.stock_levels(self.app.current_branch_id):
            status = lv.severity.value if lv.severity else "OK"
            self.tree.insert("", "end", values=(lv.medicine_code, lv.medicine_name, lv.quantity,
                                                lv.reorder_level, status),
                             tags=(status,))
