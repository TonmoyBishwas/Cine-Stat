"""BaseTab - the shared parent class of all five tabs.

Syllabus Class 4 and 8: abstraction, inheritance, and organising GUI code.
"""

from abc import ABC, abstractmethod
from tkinter import ttk

from .theme import FALLBACK_MUTED


def muted_colour(widget, dark=FALLBACK_MUTED["dark"],
                 light=FALLBACK_MUTED["light"]):
    """A grey for secondary text that stays readable on any background.

    In the Windows build this normally answers straight away: the application
    has a WindowsTheme, the theme has a palette, and the palette already knows
    which grey belongs on this window. The calculation underneath is the
    fallback for the same source file running somewhere there is no theme -
    macOS, where the window turns dark at sunset on its own, or a bare test
    that builds one widget without an application around it.

    In that case we ask the window what colour it is actually painted, average
    the red, green and blue to get its brightness, and pick the grey that
    shows up against it.
    """
    palette = palette_of(widget)
    if palette is not None:
        return palette.muted
    try:
        background = widget.winfo_toplevel().cget("background")
        red, green, blue = widget.winfo_rgb(background)
    except Exception:
        return light                 # no idea - assume a normal light window
    # winfo_rgb answers 0-65535 per channel; 128 is the midpoint of 0-255.
    brightness = (red + green + blue) / 3 / 257
    return dark if brightness < 128 else light


def palette_of(widget):
    """The Palette this widget is being drawn with, or None.

    The theme is held by the application window, so any widget can find it by
    climbing to the top of its own family tree. Written as a plain function
    rather than a method so that `muted_colour` above can use it too.
    """
    try:
        theme = getattr(widget.winfo_toplevel(), "theme", None)
    except Exception:
        return None
    return getattr(theme, "palette", None)


class BaseTab(ttk.Frame, ABC):
    """Abstract parent for every tab in the window.

    It inherits from TWO parents (multiple inheritance again):
      * ttk.Frame - so a tab really IS a rectangle of the window
      * ABC       - so we can force every tab to provide build_ui()

    It also gives every tab easy access to the shared data through `self.movies`
    and `self.predictor`, and to the shared look through `self.theme`, so no
    tab has to load the CSV or work out a colour for itself.
    """

    title = "Tab"

    def __init__(self, parent, app):
        self.app = app               # a link back to the main window
        super().__init__(parent, padding=app.theme.px(14))
        self.build_ui()

    # ---- shortcuts to the things the app already prepared -----------------

    @property
    def movies(self):
        """The MovieCollection holding every film."""
        return self.app.movies

    @property
    def predictor(self):
        """The trained SuccessPredictor."""
        return self.app.predictor

    @property
    def theme(self):
        """The WindowsTheme: colours, fonts and DPI-scaled sizes."""
        return self.app.theme

    @property
    def palette(self):
        """A shortcut, because tabs ask for colours far more than fonts."""
        return self.app.theme.palette

    def px(self, pixels):
        """Scale a pixel measurement for this screen. See theme.px()."""
        return self.app.theme.px(pixels)

    # ---- the method every tab must write ----------------------------------

    @abstractmethod
    def build_ui(self):
        """Create this tab's widgets. Each subclass does this differently."""

    # ---- a small shared helper --------------------------------------------

    def add_heading(self, text, subtitle=""):
        """Put a title (and optional explanation) at the top of the tab."""
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=(0, self.px(12)))
        ttk.Label(frame, text=text, style="Heading.TLabel").pack(anchor="w")
        if subtitle:
            ttk.Label(frame, text=subtitle, style="Muted.TLabel",
                      wraplength=self.px(900), justify="left").pack(
                          anchor="w", pady=(self.px(3), 0))
        return frame

    # NOTE: do NOT add a __str__ method to a Tkinter widget class.
    # Tkinter calls str(widget) internally to get the widget's path name, so
    # overriding __str__ here makes lines like notebook.add(tab) fail with
    # 'bad window path name'. We override __repr__ instead, which is safe.
    def __repr__(self):
        return f"{self.__class__.__name__}(title={self.title!r})"
