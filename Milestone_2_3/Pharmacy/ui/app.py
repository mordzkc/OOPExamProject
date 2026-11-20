"""Main window: top bar (branch and staff id), notebook of task screens, status bar."""
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from ..domain.exceptions import PharmacyError, ValidationError
from .lowstock_frame import LowStockFrame
from .medicine_frame import MedicineFrame
from .prescription_frame import PrescriptionFrame
from .stock_frame import StockFrame
from .validators import code_from_choice


class MainWindow(tk.Tk):
    """Owns the services object and the shared state that every screen needs."""

    def __init__(self, services):
        super().__init__()
        self.svc = services                      # the only door into the domain and database
        self.title("UCU Campus Pharmacy System")
        self.geometry("1040x680")
        self.minsize(940, 600)
        self.branch_var = tk.StringVar()
        self.staff_var = tk.StringVar(value="ST-01")   # fictional staff id
        self.status_var = tk.StringVar(value="Ready.")
        self._style()
        self._build_topbar()
        self._build_tabs()
        self._build_statusbar()
        self.reload_branches()
        self.refresh_all()

    # ------------------------------------------------------------ layout
    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=24, font=("Helvetica", 10))
        style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        style.configure("TNotebook.Tab", padding=(14, 6), font=("Helvetica", 10, "bold"))
        style.configure("Accent.TButton", font=("Helvetica", 10, "bold"))

    def _build_topbar(self):
        bar = ttk.Frame(self, padding=(10, 8))
        bar.pack(fill="x")
        ttk.Label(bar, text="Branch:").pack(side="left")
        self.branch_box = ttk.Combobox(bar, textvariable=self.branch_var, state="readonly", width=28)
        self.branch_box.pack(side="left", padx=(4, 6))
        self.branch_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_all())
        ttk.Button(bar, text="New branch", command=self.on_new_branch).pack(side="left")
        ttk.Label(bar, text="Staff ID:").pack(side="left", padx=(24, 0))
        ttk.Entry(bar, textvariable=self.staff_var, width=10).pack(side="left", padx=4)

    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 6))
        self.frames = [MedicineFrame(self.notebook, self), StockFrame(self.notebook, self),
                       PrescriptionFrame(self.notebook, self), LowStockFrame(self.notebook, self)]
        for frame, title in zip(self.frames, ("Medicines", "Stock", "Prescriptions", "Low Stock")):
            self.notebook.add(frame, text=title)

    def _build_statusbar(self):
        self.status_label = tk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken",
                                     bd=1, padx=8, pady=3, fg="#1b5e20")
        self.status_label.pack(fill="x", side="bottom")

    # ------------------------------------------------------------ shared state
    @property
    def current_branch_id(self) -> str:
        """The branch picked in the top bar, e.g. 'B01'. Raises if none is selected."""
        return code_from_choice(self.branch_var.get(), "Branch")

    def reload_branches(self):
        branches = self.svc.repos.branches.list()
        self.branch_box["values"] = [f"{b.branch_id} - {b.name}" for b in branches]
        if branches and not self.branch_var.get():
            self.branch_var.set(self.branch_box["values"][0])

    def refresh_all(self):
        """Re-read the database into every screen (called after any change)."""
        for frame in self.frames:
            frame.refresh()

    # ------------------------------------------------------------ feedback
    def set_status(self, message: str, error: bool = False):
        self.status_var.set(message)
        self.status_label.configure(fg="#b71c1c" if error else "#1b5e20")

    def run(self, action, error_title: str = "Action rejected") -> bool:
        """Run one user action. A PharmacyError becomes a dialog plus a red status line.

        The action may return a success message (str). Returns True when the action succeeded.
        """
        try:
            message = action()
        except PharmacyError as err:                      # every business rule failure lands here
            self.set_status(str(err), error=True)
            messagebox.showerror(error_title, str(err))
            return False
        self.set_status(message if isinstance(message, str) else "Done.")
        return True

    def on_new_branch(self):
        def action():
            branch_id = simpledialog.askstring("New branch", "Branch id (for example B03):", parent=self)
            if branch_id is None:
                return None
            name = simpledialog.askstring("New branch", "Branch name:", parent=self)
            if name is None:
                return None
            branch = self.svc.branches.register(branch_id, name)
            self.reload_branches()
            return f"Branch {branch.branch_id} registered."
        self.run(action, "Branch rejected")
