"""MovieApp - the main window that holds the five tabs.

Syllabus Class 7 and 8: the top level of the interface, and the place where
the data is loaded once and shared with every tab.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from ..loaders import DataLoader
from ..predictor import SuccessPredictor
from ..utils import ExportSession
from ..exceptions import MovieDataError

from .browse_tab import BrowseTab
from .charts_tab import ChartsTab
from .compare_tab import CompareTab
from .predict_tab import PredictTab
from .recommend_tab import RecommendTab


class MovieApp(tk.Tk):
    """The application window.

    It inherits from tk.Tk, so an instance of this class IS the window.
    Its job is to load the data once, train the model once, and then hand
    both to the tabs. No tab loads its own copy of the data.
    """

    TAB_CLASSES = [BrowseTab, ChartsTab, CompareTab, PredictTab, RecommendTab]

    def __init__(self, data_path):
        super().__init__()
        self.title("CineStat - Movie Analysis")
        self.geometry("1150x740")
        self.minsize(950, 640)

        self.data_path = Path(data_path)
        self.movies = None
        self.predictor = None

        self._build_status_bar()
        if not self._load_data():
            return
        self._build_menu()
        self._build_tabs()

    # ---- start up ---------------------------------------------------------

    def _build_status_bar(self):
        self.status = ttk.Label(self, text="Starting up...", anchor="w",
                                padding=(10, 5), relief="sunken")
        self.status.pack(side="bottom", fill="x")

    def _set_status(self, text):
        """Show a message at the bottom and redraw immediately."""
        self.status.config(text=text)
        self.update_idletasks()

    def _load_data(self):
        """Read the CSV and train the model. Returns False if it failed."""
        try:
            self._set_status(f"Loading {self.data_path.name}...")
            # The factory picks CSVLoader or TMDBLoader by looking at the
            # file's columns, so the app opens either dataset unchanged.
            self.movies = DataLoader.for_file(self.data_path).to_collection()

            self._set_status(f"Training the model on {len(self.movies):,} films...")
            self.predictor = SuccessPredictor(self.movies)
            self.predictor.train()
        except MovieDataError as error:
            messagebox.showerror("Could not start CineStat", str(error))
            self.destroy()
            return False

        first_year, last_year = self.movies.year_bounds()
        self._set_status(
            f"Ready - {len(self.movies):,} films from {first_year} to {last_year}  |  "
            f"model R-squared {self.predictor.r2:.3f}")
        return True

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export current view as CSV...",
                              command=lambda: self.export("csv"))
        file_menu.add_command(label="Export current view as JSON...",
                              command=lambda: self.export("json"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About CineStat", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook = notebook

        self.tabs = {}
        # POLYMORPHISM again: every tab class is built the same way, even
        # though each one draws something completely different.
        for tab_class in self.TAB_CLASSES:
            tab = tab_class(notebook, self)
            notebook.add(tab, text=tab_class.title)
            self.tabs[tab_class.title] = tab

    # ---- menu actions -----------------------------------------------------

    def active_tab(self):
        """The tab on screen right now, if it has rows worth exporting.

        Browse and Recommend both provide a method called `current_rows()`.
        Because they do, this method can hand back either one and `export()`
        below does not need to know which it got - it just calls the method.
        Python calls that DUCK TYPING: "if it answers current_rows(), it is
        exportable". It is polymorphism without needing a shared base class.
        """
        try:
            widget = self.nametowidget(self.notebook.select())
        except Exception:
            return self.tabs["Browse"]
        if hasattr(widget, "current_rows"):
            return widget
        return self.tabs["Browse"]

    def export(self, file_format):
        """Save the rows currently shown on whichever tab is open.

        Uses the ExportSession context manager, so the file is always closed
        properly even if writing goes wrong.
        """
        tab = self.active_tab()
        rows = tab.current_rows()
        if not rows:
            messagebox.showinfo("Nothing to export",
                                f"There is nothing to export on the "
                                f"{tab.title} tab yet.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=f".{file_format}",
            initialfile=f"cinestat_export.{file_format}",
            filetypes=[(f"{file_format.upper()} file", f"*.{file_format}")])
        if not path:
            return                      # the user pressed Cancel

        try:
            with ExportSession(path) as session:
                written = session.write(rows)
        except MovieDataError as error:
            messagebox.showerror("Export failed", str(error))
            return

        self._set_status(f"Exported {written:,} rows to {path}")
        messagebox.showinfo("Export complete",
                            f"Saved {written:,} rows to:\n{path}")

    def show_about(self):
        messagebox.showinfo(
            "About CineStat",
            "CineStat - Movie Analysis\n\n"
            "DS 1116 - Object Oriented Programming for Data Science Laboratory\n\n"
            f"Films loaded: {len(self.movies):,}\n"
            f"Years covered: {self.movies.year_bounds()[0]} to "
            f"{self.movies.year_bounds()[1]}\n"
            f"Model accuracy: R-squared {self.predictor.r2:.3f}\n\n"
            "The prediction uses only information known before a film is "
            "released, so it never peeks at reviews or vote counts.\n\n"
            "The Recommend tab scores films against the ones you tick and "
            "explains every suggestion. The explanation can optionally be "
            "rewritten by an AI through OpenRouter - see .env.example.")
