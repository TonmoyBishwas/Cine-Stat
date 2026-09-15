"""The look of the Windows version: colours, fonts and sizes, in one place.

WHY THIS FILE EXISTS
--------------------
The original CineStat was written on a Mac, where Tkinter borrows the
operating system's own widgets and a program looks native without being asked.
On Windows it does not work out that way, and three problems have to be solved
before the program stops looking like a visitor:

1. **Dark mode.** Windows 11 has one; Tkinter does not know about it. Ten
   million Windows laptops are set to dark and CineStat used to open a sheet
   of white paper in the middle of them.

2. **The theme Tkinter reaches for.** Tk ships a "vista" theme that copies
   Windows *7* - glossy gradient buttons and a blue glow round whatever has
   the keyboard focus. Next to Windows 11, which is flat, it looks like a
   program someone forgot to update. It also cannot be recoloured at all: the
   drawing is done by Windows itself, so a dark vista button is impossible.

   So this file uses **clam**, the one built-in theme that lets every colour
   be set, and repaints it to match Windows 11 - flat surfaces, thin borders,
   the user's own accent colour. One theme, two colour schemes, and light mode
   and dark mode are the same program rather than two different-looking ones.

3. **Size.** Once `platform_ui.set_dpi_awareness()` has told Windows to stop
   magnifying the window, every measurement written in pixels is suddenly too
   small on a 150% laptop. `px()` below is the answer: every pixel
   measurement in the interface goes through it.

WHAT IS IN HERE
---------------
  * `Palette`       - one class holding the colours of one look
  * `LIGHT` / `DARK`- the two instances of it
  * `WindowsTheme`  - applies a palette to the whole application

Syllabus topics demonstrated here:
  Class 2/3 - a class with a constructor, instance variables and a property
  Class 3   - COMPOSITION: a WindowsTheme *has a* Palette
  Class 11  - a dictionary of settings handed to a widget with **
"""

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from . import platform_ui


#: The two greys `base_tab.muted_colour()` falls back to when there is no
#: theme to ask - a bare widget built by a test, or this same source file
#: running on macOS, where the window goes dark at sunset on its own. They
#: live here rather than in base_tab.py so that this module really is the
#: only place in the interface where a colour is written down.
FALLBACK_MUTED = {"dark": "#9A9A9A", "light": "#555555"}


class Palette:
    """Every colour one version of the interface needs.

    Two instances of this class exist - LIGHT and DARK - and swapping one for
    the other changes the entire look of the program. Nothing anywhere else
    writes a colour down: tabs ask for `theme.palette.positive`, never for
    "#107C10". That is the whole reason this class is here, and it is what
    made dark mode possible without touching a single tab.
    """

    def __init__(self, name, window, surface, field, text, muted, border,
                 button, hover, pressed, accent, accent_text,
                 positive, negative, warning, stripe, first_wins, second_wins):
        self.name = name
        self.window = window            # the window behind everything
        self.surface = surface          # panels and boxes sitting on it
        self.field = field              # anything typed into or scrolled
        self.text = text
        self.muted = muted              # second-rank text: hints, captions
        self.border = border
        self.button = button
        self.hover = hover
        self.pressed = pressed
        self.accent = accent            # Windows' own accent colour
        self.accent_text = accent_text  # what can be read on top of it
        self.positive = positive        # a profit, a hit, a win
        self.negative = negative        # a loss, a flop
        self.warning = warning          # break-even: neither one nor the other
        self.stripe = stripe            # every other row of a table
        self.first_wins = first_wins    # the Compare tab's two highlights
        self.second_wins = second_wins

    @property
    def is_dark(self):
        """True if this is the dark look. Used to pick a matching title bar."""
        return self.name == "dark"

    def replace(self, **changes):
        """A copy of this palette with some colours changed.

        Used to drop the user's own Windows accent colour into a palette
        without editing the shared LIGHT and DARK objects, which everything
        else is looking at.
        """
        settings = dict(vars(self))
        settings.update(changes)
        settings["name"] = changes.get("name", self.name)
        return Palette(**settings)

    def __repr__(self):
        return f"Palette(name={self.name!r})"


#: Windows 11 light mode: #F3F3F3 behind the window, white panels on top.
LIGHT = Palette(
    name="light",
    window="#F3F3F3", surface="#FFFFFF", field="#FFFFFF",
    text="#1A1A1A", muted="#5D5D5D", border="#D6D6D6",
    button="#FDFDFD", hover="#F0F0F0", pressed="#E6E6E6",
    accent="#0078D4", accent_text="#FFFFFF",
    positive="#107C10", negative="#C42B1C", warning="#8A6A00",
    stripe="#F6F8FA", first_wins="#E4F2E6", second_wins="#E3EEF9")

#: Windows 11 dark mode. The greys are Microsoft's own: #202020 for the
#: window, #2B2B2B for anything you can type into.
DARK = Palette(
    name="dark",
    window="#202020", surface="#272727", field="#2B2B2B",
    text="#F2F2F2", muted="#A9A9A9", border="#3D3D3D",
    button="#2D2D2D", hover="#383838", pressed="#252525",
    accent="#0078D4", accent_text="#FFFFFF",
    positive="#6CCB5F", negative="#FF8A8A", warning="#FFD166",
    stripe="#242424", first_wins="#22331E", second_wins="#1E2D3D")


class WindowsTheme:
    """Dresses the whole application to look like a Windows 11 program.

    COMPOSITION (Class 3): a theme *has a* Palette. It does not inherit from
    one, because a theme is not a kind of colour - it is the thing that knows
    where each colour goes.

    Built once by MovieApp and then shared with every tab, exactly the way the
    MovieCollection and the SuccessPredictor are.
    """

    #: Point sizes, before DPI scaling. Windows itself writes menus and
    #: buttons in 9 point Segoe UI; 10 is easier to read in a long table.
    BODY_SIZE = 9
    CONTENT_SIZE = 10
    HEADING_SIZE = 15
    BIG_SIZE = 30
    VERDICT_SIZE = 20

    #: The tags that make every other row of a table slightly darker. Windows
    #: tables have done this since Explorer had a details view.
    STRIPE_TAGS = ("cinestat_even", "cinestat_odd")

    #: The colours the charts draw their bars and lines in. The dark set is
    #: the same six hues lifted several steps: a mid-tone blue that reads
    #: perfectly well on white paper goes muddy against a #272727 panel, and
    #: plain black - which is what matplotlib reaches for by default when it
    #: wants a reference line - disappears altogether.
    CHART_COLOURS = {
        "light": {"blue": "#4C72B0", "green": "#55A868", "red": "#C44E52",
                  "purple": "#8172B2", "rule": "#D1495B", "guide": "#1A1A1A"},
        "dark": {"blue": "#7AA5E8", "green": "#6FCB74", "red": "#E8756F",
                 "purple": "#AC9BE0", "rule": "#FF7A7A", "guide": "#E0E0E0"},
    }

    def __init__(self, root, mode=None, scale=None):
        self.root = root
        self.mode = mode or platform_ui.system_theme()
        self.scale = scale if scale else platform_ui.screen_scale(root)

        base = DARK if self.mode == "dark" else LIGHT
        self.palette = self._with_system_accent(base)

        self.style = ttk.Style(root)
        self._families = set(tkfont.families(root))
        # Segoe UI is the Windows typeface. The fallbacks are for the same
        # source file running on macOS or Linux, where it does not exist.
        self.family = self._first_available(
            "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Helvetica")
        self.semibold_family = self._first_available(
            "Segoe UI Semibold", self.family)
        # Windows writes big numbers in a *lighter* weight, not a heavier one.
        self.display_family = self._first_available(
            "Segoe UI Light", "Segoe UI", self.family)

    # ---- small helpers ----------------------------------------------------

    def _first_available(self, *names):
        """The first of these font families this computer actually has."""
        for name in names:
            if name in self._families:
                return name
        return names[-1]

    def _with_system_accent(self, palette):
        """Use the accent colour the user chose in Windows Settings.

        Someone who has set their Windows to purple gets purple buttons, the
        same as in every other program on their machine. `readable_on` then
        works out whether the writing on that button should be black or white,
        so a bright yellow accent does not produce white-on-yellow.
        """
        accent = platform_ui.accent_colour()
        if not accent:
            return palette
        return palette.replace(accent=accent,
                               accent_text=platform_ui.readable_on(accent))

    def px(self, pixels):
        """Scale a pixel measurement for this screen.

        Written for a 100% screen and multiplied up from there, so a table
        column that is 250 pixels wide on one laptop is 375 on a 150% one and
        holds exactly as many letters.
        """
        return int(round(pixels * self.scale))

    def font(self, size=None, weight="normal", display=False):
        """A font tuple ready to hand to a widget.

        Sizes stay in *points*: Tk turns points into pixels using the scaling
        factor set in `_apply_scaling` below, so fonts scale on a high-DPI
        screen without being multiplied here.
        """
        if display:
            family = self.display_family
        elif weight == "bold":
            family = self.semibold_family
        else:
            family = self.family
        size = self.BODY_SIZE if size is None else size
        # Segoe UI Semibold is already semi-bold; asking for bold on top of it
        # makes Windows synthesise a smeared fake bold.
        if weight == "bold" and family == self.semibold_family \
                and family != self.family:
            return (family, size)
        return (family, size, weight) if weight != "normal" else (family, size)

    # ---- the one method the application calls -----------------------------

    def apply(self):
        """Repaint everything. Called once, before any tab is built."""
        self._apply_scaling()
        self._apply_named_fonts()
        self._apply_ttk_styles()
        self._apply_plain_widget_defaults()
        self.root.configure(background=self.palette.window)
        platform_ui.use_dark_titlebar(self.root, self.palette.is_dark)
        return self

    # ---- the pieces of it -------------------------------------------------

    def _apply_scaling(self):
        """Tell Tk how many pixels there are in a point on this screen.

        Tk assumes 72 points to the inch and, left alone, 96 pixels to the
        inch. On a 150% laptop there are really 144, so every font comes out
        two thirds of the size it should be once we have taken DPI awareness.
        """
        try:
            self.root.tk.call("tk", "scaling", self.scale * 96 / 72)
        except tk.TclError:
            pass

    def _apply_named_fonts(self):
        """Point Tk's built-in font names at Segoe UI.

        Menus, dialog boxes and message boxes are drawn by Tk using these
        names, and none of them go through our own `font()` method - so this
        is the only way to reach them.
        """
        for name, size in (("TkDefaultFont", self.BODY_SIZE),
                           ("TkTextFont", self.BODY_SIZE),
                           ("TkMenuFont", self.BODY_SIZE),
                           ("TkHeadingFont", self.BODY_SIZE),
                           ("TkTooltipFont", self.BODY_SIZE),
                           ("TkIconFont", self.BODY_SIZE)):
            try:
                tkfont.nametofont(name, root=self.root).configure(
                    family=self.family, size=size)
            except tk.TclError:
                pass

    def _apply_ttk_styles(self):
        """Recolour every ttk widget the program uses."""
        style, colour = self.style, self.palette

        # clam is the only built-in theme whose colours can all be set. See
        # the note at the top of this file for why we do not use "vista".
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass                      # some stripped-down Tk build - carry on

        body = self.font()
        content = self.font(self.CONTENT_SIZE)

        style.configure(".", background=colour.window, foreground=colour.text,
                        fieldbackground=colour.field, font=body,
                        bordercolor=colour.border, darkcolor=colour.window,
                        lightcolor=colour.window, troughcolor=colour.field,
                        focuscolor=colour.accent, relief="flat")

        style.configure("TFrame", background=colour.window)
        style.configure("TLabel", background=colour.window,
                        foreground=colour.text)
        style.configure("TSeparator", background=colour.border)
        style.configure("TSizegrip", background=colour.window)

        # ---- boxes with a title round them --------------------------------
        style.configure("TLabelframe", background=colour.window,
                        bordercolor=colour.border, relief="solid",
                        borderwidth=1)
        style.configure("TLabelframe.Label", background=colour.window,
                        foreground=colour.muted, font=self.font(weight="bold"))

        # ---- buttons ------------------------------------------------------
        # Windows 11 buttons are flat, with a one-pixel border and a slightly
        # lighter face when the mouse is over them.
        style.configure("TButton", background=colour.button,
                        foreground=colour.text, bordercolor=colour.border,
                        relief="flat", borderwidth=1, focusthickness=0,
                        padding=(self.px(12), self.px(5)), anchor="center")
        style.map("TButton",
                  background=[("disabled", colour.window),
                              ("pressed", colour.pressed),
                              ("active", colour.hover)],
                  foreground=[("disabled", colour.muted)],
                  bordercolor=[("active", colour.accent),
                               ("focus", colour.accent)])

        # The one button on each tab that does the thing the tab is for.
        # Windows calls this the "accent button" and paints it in the user's
        # own accent colour.
        style.configure("Accent.TButton", background=colour.accent,
                        foreground=colour.accent_text,
                        bordercolor=colour.accent,
                        font=self.font(weight="bold"))
        style.map("Accent.TButton",
                  background=[("disabled", colour.border),
                              ("pressed", colour.accent),
                              ("active", colour.accent)],
                  foreground=[("disabled", colour.muted),
                              ("active", colour.accent_text)])

        # ---- things you type into -----------------------------------------
        for widget in ("TEntry", "TCombobox", "TSpinbox"):
            style.configure(widget, foreground=colour.text,
                            fieldbackground=colour.field,
                            background=colour.button,
                            bordercolor=colour.border,
                            arrowcolor=colour.text,
                            insertcolor=colour.text,
                            selectbackground=colour.accent,
                            selectforeground=colour.accent_text,
                            padding=(self.px(6), self.px(4)))
            style.map(widget,
                      bordercolor=[("focus", colour.accent),
                                   ("hover", colour.accent)],
                      fieldbackground=[("readonly", colour.field),
                                       ("disabled", colour.window)],
                      foreground=[("disabled", colour.muted)],
                      arrowcolor=[("disabled", colour.muted)])
        # A read-only Combobox keeps the chosen line highlighted in blue after
        # the dropdown closes, which looks like a mistake. Matching the
        # highlight to the field hides it.
        style.map("TCombobox",
                  selectbackground=[("readonly", colour.field)],
                  selectforeground=[("readonly", colour.text)])

        # ---- the tab strip ------------------------------------------------
        style.configure("TNotebook", background=colour.window,
                        bordercolor=colour.border, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", background=colour.window,
                        foreground=colour.muted, bordercolor=colour.border,
                        padding=(self.px(18), self.px(8)),
                        font=self.font(self.CONTENT_SIZE))
        # clam gives the SELECTED tab a padding of its own ("6 4 6 2"), which
        # overrides the padding configured above and drops the open tab a few
        # pixels below its neighbours - it reads as a rendering fault rather
        # than as a design. Mapping the same padding onto the selected state
        # keeps the whole strip level.
        tab_padding = (self.px(18), self.px(8))
        style.map("TNotebook.Tab",
                  background=[("selected", colour.surface),
                              ("active", colour.hover)],
                  foreground=[("selected", colour.text)],
                  padding=[("selected", tab_padding)],
                  expand=[("selected", (0, 0, 0, 0))])

        # ---- tables -------------------------------------------------------
        # A row has to be tall enough for 10 point Segoe UI plus breathing
        # room; Tk's default of 20 pixels clips the descenders.
        style.configure("Treeview", background=colour.surface,
                        fieldbackground=colour.surface,
                        foreground=colour.text, borderwidth=1,
                        bordercolor=colour.border, relief="solid",
                        rowheight=self.px(26), font=content)
        style.map("Treeview",
                  background=[("selected", colour.accent)],
                  foreground=[("selected", colour.accent_text)])
        style.configure("Treeview.Heading", background=colour.window,
                        foreground=colour.muted, relief="flat",
                        borderwidth=0, padding=(self.px(6), self.px(6)),
                        font=self.font(weight="bold"))
        style.map("Treeview.Heading",
                  background=[("active", colour.hover)],
                  foreground=[("active", colour.text)])

        # ---- scrollbars ---------------------------------------------------
        # Windows 11 scrollbars are a thin grey bar with no arrows at the ends.
        style.configure("Vertical.TScrollbar", background=colour.border,
                        troughcolor=colour.window, bordercolor=colour.window,
                        arrowcolor=colour.muted, relief="flat",
                        borderwidth=0, width=self.px(12))
        style.configure("Horizontal.TScrollbar", background=colour.border,
                        troughcolor=colour.window, bordercolor=colour.window,
                        arrowcolor=colour.muted, relief="flat", borderwidth=0)
        for bar in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.map(bar, background=[("pressed", colour.accent),
                                       ("active", colour.muted)])

        style.configure("TProgressbar", background=colour.accent,
                        troughcolor=colour.field, bordercolor=colour.border,
                        borderwidth=0, thickness=self.px(6))

        # ---- named label styles the tabs ask for by name ------------------
        style.configure("Heading.TLabel",
                        font=self.font(self.HEADING_SIZE, "bold"))
        style.configure("Muted.TLabel", foreground=colour.muted)
        style.configure("Big.TLabel",
                        font=self.font(self.BIG_SIZE, display=True))
        style.configure("Verdict.TLabel",
                        font=self.font(self.VERDICT_SIZE, "bold"))
        style.configure("Value.TLabel",
                        font=self.font(self.CONTENT_SIZE, "bold"))
        style.configure("Status.TLabel", background=colour.surface,
                        foreground=colour.muted, relief="flat")
        style.configure("Card.TFrame", background=colour.surface)

    def _apply_plain_widget_defaults(self):
        """Colour the widgets that are not ttk widgets at all.

        `tk.Listbox`, `tk.Text` and `tk.Menu` are the old Tk widgets, and ttk
        styles do not reach them. Tk's option database does: these lines set
        the default for every one of them created from now on, so no tab has
        to remember. The dropdown list hanging off a Combobox is one of these
        too - it is a Listbox, which is why it needs its own line.
        """
        colour = self.palette
        defaults = {
            "*TCombobox*Listbox.background": colour.field,
            "*TCombobox*Listbox.foreground": colour.text,
            "*TCombobox*Listbox.selectBackground": colour.accent,
            "*TCombobox*Listbox.selectForeground": colour.accent_text,
            "*Menu.background": colour.surface,
            "*Menu.foreground": colour.text,
            "*Menu.activeBackground": colour.accent,
            "*Menu.activeForeground": colour.accent_text,
            "*Menu.selectColor": colour.text,
            "*Menu.relief": "flat",
            "*Menu.borderWidth": 1,
        }
        for pattern, value in defaults.items():
            try:
                self.root.option_add(pattern, value)
            except tk.TclError:
                pass

    # ---- settings handed to widgets that style themselves ------------------

    def text_options(self):
        """Colours for a tk.Text box, ready to be unpacked with **.

        Note that the background and the foreground are always set *together*.
        Setting only one of them is the bug described in README.md: the
        explanation box asked for a near-white background, left the text
        colour alone, and in dark mode rendered white on white.
        """
        colour = self.palette
        return dict(background=colour.field, foreground=colour.text,
                    insertbackground=colour.text,
                    selectbackground=colour.accent,
                    selectforeground=colour.accent_text,
                    highlightthickness=0, borderwidth=0,
                    font=self.font(self.CONTENT_SIZE))

    def listbox_options(self):
        """The same, for a tk.Listbox."""
        colour = self.palette
        return dict(background=colour.field, foreground=colour.text,
                    selectbackground=colour.accent,
                    selectforeground=colour.accent_text,
                    highlightthickness=0, borderwidth=0,
                    font=self.font(self.CONTENT_SIZE))

    def menu_options(self):
        """The same, for a tk.Menu."""
        colour = self.palette
        return dict(background=colour.surface, foreground=colour.text,
                    activebackground=colour.accent,
                    activeforeground=colour.accent_text,
                    disabledforeground=colour.muted,
                    relief="flat", borderwidth=1, tearoff=0)

    # ---- tables -----------------------------------------------------------

    def prepare_table(self, tree):
        """Set up the two tags that make every other row slightly darker."""
        even, odd = self.STRIPE_TAGS
        tree.tag_configure(even, background=self.palette.surface)
        tree.tag_configure(odd, background=self.palette.stripe)

    def stripe_row(self, index):
        """Which of the two tags row number `index` should carry."""
        return self.STRIPE_TAGS[index % 2]

    # ---- charts -----------------------------------------------------------

    def chart(self, name):
        """One of the chart colours, picked for the current light or dark look.

            self.theme.chart("green")   ->  "#55A868" or "#6FCB74"
        """
        return self.CHART_COLOURS[self.palette.name][name]

    def style_figure(self, figure):
        """Make a matplotlib figure sit on the window instead of on paper.

        Matplotlib draws on a white sheet by default. Inside a dark window
        that is a torch shining out of the middle of the tab, so the figure,
        the axes, the ticks, the labels and the legend all have to be told
        about the palette - matplotlib has no idea Tkinter exists.
        """
        colour = self.palette
        figure.patch.set_facecolor(colour.surface)
        for axes in figure.get_axes():
            self.style_axes(axes)

    def style_axes(self, axes):
        """Recolour one chart: its background, frame, ticks and writing."""
        colour = self.palette
        axes.set_facecolor(colour.surface)
        for spine in ("top", "right"):
            axes.spines[spine].set_visible(False)      # Windows 11 is spare
        for spine in ("left", "bottom"):
            axes.spines[spine].set_color(colour.border)
        axes.tick_params(colors=colour.muted, labelsize=8)
        axes.xaxis.label.set_color(colour.muted)
        axes.yaxis.label.set_color(colour.muted)
        axes.title.set_color(colour.text)
        axes.grid(True, axis="both", color=colour.border,
                  linewidth=0.6, alpha=0.5)
        axes.set_axisbelow(True)                       # grid behind the bars

    def style_legend(self, axes):
        """Called after a chart has added its legend, which is drawn last."""
        legend = axes.get_legend()
        if legend is None:
            return
        colour = self.palette
        legend.get_frame().set_facecolor(colour.surface)
        legend.get_frame().set_edgecolor(colour.border)
        for label in legend.get_texts():
            label.set_color(colour.text)

    def style_toolbar(self, toolbar):
        """The matplotlib zoom-and-save toolbar is made of plain Tk widgets.

        It builds itself out of tk.Button and tk.Label, so it arrives white
        whatever the rest of the window is doing. Walking its children is the
        only way in - matplotlib offers no colour setting for it.
        """
        colour = self.palette
        try:
            toolbar.configure(background=colour.window)
        except tk.TclError:
            pass

        for child in toolbar.winfo_children():
            try:
                child.configure(background=colour.window,
                                foreground=colour.text,
                                activebackground=colour.hover,
                                activeforeground=colour.text,
                                highlightbackground=colour.window,
                                # Tk greys a disabled button's icon by
                                # stippling it in disabledforeground. Left at
                                # its default that paints a white chessboard
                                # over the Back and Forward arrows, which is
                                # far more eye-catching than the buttons that
                                # actually work. In the window's own colour
                                # the stipple just fades them.
                                disabledforeground=colour.window,
                                relief="flat", borderwidth=0)
            except tk.TclError:
                # A separator or the message label: not everything in there
                # takes every one of those settings.
                for setting in ("background", "foreground"):
                    try:
                        child.configure(**{setting: colour.window
                                           if setting == "background"
                                           else colour.text})
                    except tk.TclError:
                        pass

            # The icons themselves are black PNGs. matplotlib decides whether
            # to recolour them by looking at the button's background - but it
            # does that while the toolbar is being built, which is before we
            # get here, so on a dark window they come out black on near-black.
            # Asking matplotlib to choose again, now that the button has been
            # repainted, gets us light icons.
            if getattr(child, "_image_file", None):
                try:
                    toolbar._set_image_for_button(child)
                except Exception:
                    pass          # a private method; never worth a crash

    def __repr__(self):
        return (f"WindowsTheme(mode={self.mode!r}, scale={self.scale}, "
                f"family={self.family!r})")
