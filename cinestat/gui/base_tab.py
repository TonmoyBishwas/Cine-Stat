"""BaseTab - the shared parent class of all four tabs.

Syllabus Class 4 and 8: abstraction, inheritance, and organising GUI code.
"""

from abc import ABC, abstractmethod
from tkinter import ttk


class BaseTab(ttk.Frame, ABC):
    """Abstract parent for every tab in the window.

    It inherits from TWO parents (multiple inheritance again):
      * ttk.Frame - so a tab really IS a rectangle of the window
      * ABC       - so we can force every tab to provide build_ui()

    It also gives every tab easy access to the shared data through `self.movies`
    and `self.predictor`, so no tab has to load the CSV for itself.
    """

    title = "Tab"

    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app               # a link back to the main window
        self.build_ui()

    # ---- shortcuts to the data the app already loaded ---------------------

    @property
    def movies(self):
        """The MovieCollection holding every film."""
        return self.app.movies

    @property
    def predictor(self):
        """The trained SuccessPredictor."""
        return self.app.predictor

    # ---- the method every tab must write ----------------------------------

    @abstractmethod
    def build_ui(self):
        """Create this tab's widgets. Each subclass does this differently."""

    # ---- a small shared helper --------------------------------------------

    def add_heading(self, text, subtitle=""):
        """Put a title (and optional explanation) at the top of the tab."""
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=(0, 10))
        ttk.Label(frame, text=text,
                  font=("Helvetica", 15, "bold")).pack(anchor="w")
        if subtitle:
            ttk.Label(frame, text=subtitle, foreground="#555555",
                      wraplength=900, justify="left").pack(anchor="w", pady=(2, 0))
        return frame

    # NOTE: do NOT add a __str__ method to a Tkinter widget class.
    # Tkinter calls str(widget) internally to get the widget's path name, so
    # overriding __str__ here makes lines like notebook.add(tab) fail with
    # 'bad window path name'. We override __repr__ instead, which is safe.
    def __repr__(self):
        return f"{self.__class__.__name__}(title={self.title!r})"
