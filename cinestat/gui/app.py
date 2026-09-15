"""MovieApp - the main window that holds the five tabs.

Syllabus Class 7 and 8: the top level of the interface, and the place where
the data is loaded once and shared with every tab.

This is the Windows build. Three things happen here that did not have to
happen on a Mac, and all three are explained where they are done:

  * the process claims DPI awareness before the first window exists,
  * the window is dressed by a WindowsTheme rather than left to Tk,
  * the menus carry Windows keyboard shortcuts (Ctrl, not Command) and the
    underlined letters that make Alt+F open the File menu.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from ..loaders import DataLoader
from ..predictor import SuccessPredictor
from ..utils import ExportSession
from ..exceptions import MovieDataError

from . import platform_ui
from .theme import WindowsTheme
from .browse_tab import BrowseTab
from .charts_tab import ChartsTab
from .compare_tab import CompareTab
from .predict_tab import PredictTab
from .recommend_tab import RecommendTab


def _free_mnemonic(label, taken):
    """Which letter of `label` to underline, avoiding the ones already used.

    Alt+C cannot mean both "Charts" and "Compare", so the second one moves
    along to its next free letter. Returns the position to pass to a menu's
    `underline=`, and remembers the letter it chose in `taken`.
    """
    for position, letter in enumerate(label.lower()):
        if letter.isalpha() and letter not in taken:
            taken.add(letter)
            return position
    return 0


class MovieApp(tk.Tk):
    """The application window.

    It inherits from tk.Tk, so an instance of this class IS the window.
    Its job is to load the data once, train the model once, build the look
    once, and then hand all three to the tabs. No tab loads its own copy of
    the data and no tab works out its own colours.
    """

    TAB_CLASSES = [BrowseTab, ChartsTab, CompareTab, PredictTab, RecommendTab]

    #: Written for a 100% screen; multiplied up by the theme on a high-DPI one.
    WINDOW_WIDTH = 1180
    WINDOW_HEIGHT = 760
    MINIMUM_WIDTH = 980
    MINIMUM_HEIGHT = 660

    def __init__(self, data_path, theme_mode=None, ui_scale=None):
        # Before anything else, and before a window exists: tell Windows we
        # will do our own scaling, and claim our own taskbar button. Doing
        # this after the first window has been drawn is too late.
        platform_ui.prepare_process()

        super().__init__()

        # The look has to exist before any widget does, because BaseTab asks
        # it for its own padding.
        self.theme = WindowsTheme(self, mode=theme_mode, scale=ui_scale).apply()

        self.title("CineStat - Movie Analysis")
        platform_ui.set_window_icon(self)
        platform_ui.centre_on_screen(self, self.theme.px(self.WINDOW_WIDTH),
                                     self.theme.px(self.WINDOW_HEIGHT))
        self.minsize(self.theme.px(self.MINIMUM_WIDTH),
                     self.theme.px(self.MINIMUM_HEIGHT))

        self.data_path = Path(data_path)
        self.movies = None
        self.predictor = None

        self._build_status_bar()
        if not self._load_data():
            return
        self._build_menu()
        self._build_tabs()
        self._bind_shortcuts()

    # ---- start up ---------------------------------------------------------

    def _build_status_bar(self):
        """The strip along the bottom, with a resize grip in the corner.

        The grip is a Windows habit worth keeping: it is the corner you drag
        to resize a window, and its absence is one of those small things that
        makes a program feel foreign without anyone being able to say why.
        """
        bar = ttk.Frame(self, style="Card.TFrame")
        bar.pack(side="bottom", fill="x")
        ttk.Separator(self, orient="horizontal").pack(side="bottom", fill="x")

        self.status = ttk.Label(bar, text="Starting up...", anchor="w",
                                style="Status.TLabel",
                                padding=(self.theme.px(12), self.theme.px(5)))
        self.status.pack(side="left", fill="x", expand=True)
        ttk.Sizegrip(bar).pack(side="right", padx=(0, self.theme.px(2)))

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
        """The menu bar, written the way Windows writes one.

        Two Windows conventions are followed here that the Mac build had no
        need of:

        * `underline=` puts the line under one letter of each entry, so Alt+F
          opens File and Alt+X closes the program. Windows users reach for
          this without thinking about it.
        * `accelerator=` writes the shortcut down the right-hand side of the
          menu. It only *writes* it - Tk does not bind anything - which is
          why `_bind_shortcuts` below binds exactly the same list. Both come
          from `platform_ui.shortcut()`, so the menu cannot end up advertising
          a key that does nothing.
        """
        menubar = tk.Menu(self, **self.theme.menu_options())

        file_menu = tk.Menu(menubar, **self.theme.menu_options())
        # The underlined letter is the one Alt reaches, so no two entries in
        # the same menu may share it: here C for CSV and J for JSON, both of
        # which happen to sit at character 23.
        file_menu.add_command(label="Export current view as CSV...",
                              underline=23,
                              accelerator=platform_ui.shortcut("e")[0],
                              command=lambda: self.export("csv"))
        file_menu.add_command(label="Export current view as JSON...",
                              underline=23,
                              accelerator=platform_ui.shortcut("e", shift=True)[0],
                              command=lambda: self.export("json"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", underline=1, accelerator="Alt+F4",
                              command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu, underline=0)

        view_menu = tk.Menu(menubar, **self.theme.menu_options())
        taken = set()
        for number, tab_class in enumerate(self.TAB_CLASSES, start=1):
            label = f"{tab_class.title} tab"
            view_menu.add_command(
                label=label, underline=_free_mnemonic(label, taken),
                accelerator=platform_ui.shortcut(str(number))[0],
                command=lambda name=tab_class.title: self.show_tab(name))
        menubar.add_cascade(label="View", menu=view_menu, underline=0)

        help_menu = tk.Menu(menubar, **self.theme.menu_options())
        help_menu.add_command(label="About CineStat", underline=0,
                              accelerator="F1", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu, underline=0)

        self.config(menu=menubar)

    def _bind_shortcuts(self):
        """Actually make the keys in the menu do something.

        `bind_all` rather than `bind`, because the key has to work no matter
        which box on which tab happens to have the cursor in it.
        """
        self.bind_all(platform_ui.shortcut("e")[1],
                      lambda event: self.export("csv"))
        self.bind_all(platform_ui.shortcut("e", shift=True)[1],
                      lambda event: self.export("json"))
        self.bind_all("<F1>", lambda event: self.show_about())

        for number, tab_class in enumerate(self.TAB_CLASSES, start=1):
            # The default argument freezes THIS tab's name into the lambda.
            # Without it every one of the five would jump to the last tab.
            self.bind_all(platform_ui.shortcut(str(number))[1],
                          lambda event, name=tab_class.title: self.show_tab(name))

        # Ctrl+Tab walks forward through the tabs, Ctrl+Shift+Tab back - the
        # same keys that move between tabs in File Explorer and every browser.
        self.bind_all("<Control-Tab>", lambda event: self.step_tab(1))
        self.bind_all("<Control-Shift-Tab>", lambda event: self.step_tab(-1))

    def _build_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True,
                      padx=self.theme.px(12), pady=self.theme.px(12))
        self.notebook = notebook

        self.tabs = {}
        # POLYMORPHISM again: every tab class is built the same way, even
        # though each one draws something completely different.
        for tab_class in self.TAB_CLASSES:
            tab = tab_class(notebook, self)
            notebook.add(tab, text=tab_class.title)
            self.tabs[tab_class.title] = tab

    # ---- moving between tabs ----------------------------------------------

    def show_tab(self, title):
        """Bring one tab to the front by name. Used by View and by Ctrl+1-5."""
        tab = self.tabs.get(title)
        if tab is not None:
            self.notebook.select(tab)
        return "break"          # stop Tk passing the key on to the widget

    def step_tab(self, direction):
        """Move one tab left or right, wrapping round at the ends."""
        order = self.notebook.tabs()
        if not order:
            return "break"
        here = order.index(self.notebook.select())
        self.notebook.select(order[(here + direction) % len(order)])
        return "break"

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
            return "break"

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=f".{file_format}",
            initialfile=f"cinestat_export.{file_format}",
            # Windows' Save dialog shows this list in the "Save as type" box,
            # and "All files" is what users expect to find at the bottom of it.
            filetypes=[(f"{file_format.upper()} file", f"*.{file_format}"),
                       ("All files", "*.*")])
        if not path:
            return "break"              # the user pressed Cancel

        try:
            with ExportSession(path) as session:
                written = session.write(rows)
        except MovieDataError as error:
            messagebox.showerror("Export failed", str(error))
            return "break"

        self._set_status(f"Exported {written:,} rows to {path}")
        messagebox.showinfo("Export complete",
                            f"Saved {written:,} rows to:\n{path}")
        return "break"

    def show_about(self):
        first_year, last_year = self.movies.year_bounds()
        messagebox.showinfo(
            "About CineStat",
            "CineStat - Movie Analysis (Windows edition)\n\n"
            "DS 1116 - Object Oriented Programming for Data Science Laboratory\n\n"
            f"Films loaded: {len(self.movies):,}\n"
            f"Years covered: {first_year} to {last_year}\n"
            f"Model accuracy: R-squared {self.predictor.r2:.3f}\n\n"
            "The prediction uses only information known before a film is "
            "released, so it never peeks at reviews or vote counts.\n\n"
            "The Recommend tab scores films against the ones you tick and "
            "explains every suggestion. The explanation can optionally be "
            "rewritten by an AI through OpenRouter - see .env.example.\n\n"
            f"Appearance: {self.theme.mode} mode, following Windows. "
            f"Set CINESTAT_THEME=light or dark to override it.",
            parent=self)
        return "break"
