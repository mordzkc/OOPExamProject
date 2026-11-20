"""Screen S-02: register a medicine and list all medicines."""
import tkinter as tk
from tkinter import ttk

from .validators import parse_price, parse_whole_number, required

CATEGORIES = ("ORDINARY", "CONTROLLED", "NARCOTIC")


class MedicineFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.code, self.name = tk.StringVar(), tk.StringVar()
        self.price, self.reorder = tk.StringVar(), tk.StringVar(value="0")
        self.category = tk.StringVar(value=CATEGORIES[0])

        form = ttk.LabelFrame(self, text="Register medicine", padding=10)
        form.pack(fill="x")
        fields = (("Code", self.code, 12), ("Name", self.name, 28),
                  ("Unit price (UGX)", self.price, 12), ("Reorder level", self.reorder, 8))
        for col, (label, var, width) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=col, sticky="w", padx=4)
            ttk.Entry(form, textvariable=var, width=width).grid(row=1, column=col, padx=4, pady=(2, 0))
        ttk.Label(form, text="Category").grid(row=0, column=4, sticky="w", padx=4)
        ttk.Combobox(form, textvariable=self.category, values=CATEGORIES, state="readonly",
                     width=14).grid(row=1, column=4, padx=4, pady=(2, 0))
        ttk.Button(form, text="Register", style="Accent.TButton",
                   command=self.on_register).grid(row=1, column=5, padx=(14, 4))

        cols = ("code", "name", "category", "price", "reorder")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for col, text, width in (("code", "Code", 90), ("name", "Name", 260), ("category", "Category", 110),
                                 ("price", "Unit price (UGX)", 130), ("reorder", "Reorder level", 110)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))

    def on_register(self):
        def action():
            # Text is converted here; the domain then enforces price > 0, unique code and so on.
            code = required(self.code.get(), "Medicine code")
            self.app.svc.medicines.register(code, required(self.name.get(), "Medicine name"),
                                            parse_price(self.price.get()),
                                            parse_whole_number(self.reorder.get(), "Reorder level"),
                                            self.category.get())
            return f"Medicine {code.upper()} registered."
        if self.app.run(action, "Registration rejected"):
            for var in (self.code, self.name, self.price):
                var.set("")
            self.reorder.set("0")
            self.app.refresh_all()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for m in self.app.svc.repos.medicines.list():
            self.tree.insert("", "end", values=(m.code, m.name, m.category, f"{m.unit_price:,.0f}",
                                                m.reorder_level))
