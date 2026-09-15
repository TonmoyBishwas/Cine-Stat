"""BaseTab - the shared parent class of all four tabs.

Syllabus Class 4 and 8: abstraction, inheritance, and organising GUI code.
"""

from abc import ABC, abstractmethod
from tkinter import ttk


def muted_colour(widget, dark="#9A9A9A", light="#555555"):
    """A grey for secondary text that stays readable in dark mode too.

    Hard-coding "#555555" looks right on a white window and almost vanishes
    on a dark one. macOS switches the whole window to dark at sunset, so the
    colour has to be worked out at runtime rather than written down.

    We ask the window what colour it is actually painted, average the red,
    green and blue to get its brightness, and pick the grey that shows up
    against it.
    """
    try:
        background = widget.winfo_toplevel().cget("background")
        red, green, blue = widget.winfo_rgb(background)
    except Exception:
        return light                 # no idea - assume a normal light window
    # winfo_rgb answers 0-65535 per channel; 128 is the midpoint of 0-255.
    brightness = (red + green + blue) / 3 / 257
    return dark if brightness < 128 else light


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
            ttk.Label(frame, text=subtitle, foreground=muted_colour(self),
                      wraplength=900, justify="left").pack(anchor="w", pady=(2, 0))
        return frame

    # NOTE: do NOT add a __str__ method to a Tkinter widget class.
    # Tkinter calls str(widget) internally to get the widget's path name, so
    # overriding __str__ here makes lines like notebook.add(tab) fail with
    # 'bad window path name'. We override __repr__ instead, which is safe.
    def __repr__(self):
        return f"{self.__class__.__name__}(title={self.title!r})"
