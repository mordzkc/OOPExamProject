"""Screen S-05: low-stock report for one branch or all branches."""
import tkinter as tk
from tkinter import ttk

SCOPES = ("Selected branch", "All branches")


class LowStockFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.scope = tk.StringVar(value=SCOPES[1])
        self.summary = tk.StringVar()

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text="Show:").pack(side="left")
        box = ttk.Combobox(top, textvariable=self.scope, values=SCOPES, state="readonly", width=18)
        box.pack(side="left", padx=6)
        box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=6)
        ttk.Label(top, textvariable=self.summary, font=("Helvetica", 10, "bold")).pack(side="right")

        cols = ("branch", "code", "name", "qty", "reorder", "severity", "suggest")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        for col, text, width in (("branch", "Branch", 70), ("code", "Code", 90), ("name", "Medicine", 230),
                                 ("qty", "In stock", 80), ("reorder", "Reorder level", 100),
                                 ("severity", "Severity", 90), ("suggest", "Suggested order", 120)):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="w")
        self.tree.tag_configure("CRITICAL", background="#fde0e0", foreground="#8e0000")
        self.tree.tag_configure("LOW", background="#fff4d6", foreground="#7a5200")
        self.tree.pack(fill="both", expand=True, pady=(12, 0))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        branch = None
        if self.scope.get() == SCOPES[0] and self.app.branch_var.get():
            branch = self.app.current_branch_id
        names = {m.code: m.name for m in self.app.svc.repos.medicines.list()}
        items = self.app.svc.stock.low_stock(branch)
        for i in items:
            self.tree.insert("", "end", tags=(i.severity.value,),
                             values=(i.branch_id, i.medicine_code, names.get(i.medicine_code, ""),
                                     i.quantity, i.reorder_level, i.severity.value, f"+{i.suggested_reorder}"))
        critical = sum(1 for i in items if i.severity.value == "CRITICAL")
        self.summary.set(f"{len(items)} item(s) need attention, {critical} critical")
