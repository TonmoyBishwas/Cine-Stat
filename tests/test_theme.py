"""Tests for the look of the Windows build.

Two kinds of test live here. The first kind needs no window at all, because a
Palette is an ordinary object holding sixteen colours. The second kind builds
a real Tk root and checks that applying the theme to it actually changed
something - and, in particular, that the colour bugs described in README.md
are impossible to write again:

  * a widget that sets one half of a colour pair (white text on white),
  * a colour hard-coded for light mode that vanishes in dark mode.

As everywhere else in this project, the tests skip themselves on a machine
with no screen rather than failing.
"""

import unittest


def screen_available():
    """Can we actually open a window on this machine?"""
    try:
        import tkinter
        root = tkinter.Tk()
        root.destroy()
        return True
    except Exception:
        return False


HAVE_SCREEN = screen_available()


# ---------------------------------------------------------------------------
# The palette on its own - no window needed
# ---------------------------------------------------------------------------
class TestPalette(unittest.TestCase):

    def setUp(self):
        from cinestat.gui.theme import LIGHT, DARK
        self.light, self.dark = LIGHT, DARK

    def test_only_the_dark_one_says_it_is_dark(self):
        self.assertTrue(self.dark.is_dark)
        self.assertFalse(self.light.is_dark)

    def test_every_colour_is_a_hex_colour(self):
        for palette in (self.light, self.dark):
            for name, value in vars(palette).items():
                if name == "name":
                    continue
                with self.subTest(palette=palette.name, colour=name):
                    self.assertRegex(value, r"^#[0-9A-Fa-f]{6}$")

    def test_the_two_palettes_define_exactly_the_same_colours(self):
        """A colour defined in one and missing from the other is a crash
        waiting for whoever switches their computer to dark mode."""
        self.assertEqual(set(vars(self.light)), set(vars(self.dark)))

    def test_text_can_be_read_on_the_window_in_both(self):
        from cinestat.gui.platform_ui import brightness
        for palette in (self.light, self.dark):
            with self.subTest(palette=palette.name):
                gap = abs(brightness(palette.text) - brightness(palette.window))
                self.assertGreater(gap, 120,
                                   f"{palette.name}: text is unreadable on the window")

    def test_muted_text_is_dimmer_than_normal_text_but_still_visible(self):
        from cinestat.gui.platform_ui import brightness
        for palette in (self.light, self.dark):
            with self.subTest(palette=palette.name):
                gap = abs(brightness(palette.muted) - brightness(palette.window))
                self.assertGreater(gap, 40, "muted text disappears")
                self.assertLess(
                    abs(brightness(palette.muted) - brightness(palette.window)),
                    abs(brightness(palette.text) - brightness(palette.window)) + 1)

    def test_the_verdict_colours_can_be_read_on_the_window(self):
        """"Flop" in dark red on a #202020 window is the exact bug this
        catches: present in the widget, invisible to the user."""
        from cinestat.gui.platform_ui import brightness
        for palette in (self.light, self.dark):
            for name in ("positive", "negative", "warning"):
                with self.subTest(palette=palette.name, colour=name):
                    gap = abs(brightness(getattr(palette, name))
                              - brightness(palette.window))
                    self.assertGreater(gap, 40, f"{name} is invisible")

    def test_replace_makes_a_copy_and_leaves_the_original_alone(self):
        recoloured = self.dark.replace(accent="#AA00AA")
        self.assertEqual(recoloured.accent, "#AA00AA")
        self.assertEqual(self.dark.accent, "#0078D4")
        self.assertEqual(recoloured.name, "dark")
        self.assertIsNot(recoloured, self.dark)

    def test_repr_says_which_palette_it_is(self):
        self.assertIn("dark", repr(self.dark))


# ---------------------------------------------------------------------------
# The theme applied to a real window
# ---------------------------------------------------------------------------
@unittest.skipUnless(HAVE_SCREEN, "no screen available")
class TestWindowsTheme(unittest.TestCase):

    def setUp(self):
        import tkinter as tk
        from cinestat.gui.theme import WindowsTheme
        self.root = tk.Tk()
        self.root.withdraw()
        self.theme = WindowsTheme(self.root, mode="dark", scale=1.0).apply()

    def tearDown(self):
        self.root.destroy()

    # ---- which palette, and how big ---------------------------------------

    def test_asking_for_dark_gets_the_dark_palette(self):
        self.assertEqual(self.theme.palette.name, "dark")
        self.assertTrue(self.theme.palette.is_dark)

    def test_asking_for_light_gets_the_light_palette(self):
        import tkinter as tk
        from cinestat.gui.theme import WindowsTheme
        other = tk.Tk()
        other.withdraw()
        try:
            theme = WindowsTheme(other, mode="light", scale=1.0)
            self.assertEqual(theme.palette.name, "light")
        finally:
            other.destroy()

    def test_px_scales_pixel_measurements(self):
        import tkinter as tk
        from cinestat.gui.theme import WindowsTheme
        other = tk.Tk()
        other.withdraw()
        try:
            theme = WindowsTheme(other, mode="light", scale=1.5)
            self.assertEqual(theme.px(100), 150)
            self.assertEqual(theme.px(10), 15)
            self.assertIsInstance(theme.px(7), int)   # pixels are whole
        finally:
            other.destroy()

    def test_px_does_nothing_on_an_ordinary_screen(self):
        self.assertEqual(self.theme.px(250), 250)

    # ---- fonts ------------------------------------------------------------

    def test_the_font_is_the_one_this_operating_system_writes_in(self):
        from cinestat.gui import platform_ui
        if platform_ui.IS_WINDOWS:
            self.assertEqual(self.theme.family, "Segoe UI")

    def test_font_returns_something_tk_accepts(self):
        import tkinter.font as tkfont
        for wanted in (self.theme.font(),
                       self.theme.font(15, "bold"),
                       self.theme.font(30, display=True)):
            with self.subTest(font=wanted):
                # If Tk cannot parse it this raises TclError.
                tkfont.Font(root=self.root, font=wanted)

    def test_bold_is_not_asked_for_twice(self):
        """Segoe UI Semibold is already semi-bold. Asking Windows for bold on
        top of it produces a smeared synthetic bold."""
        from cinestat.gui import platform_ui
        if not platform_ui.IS_WINDOWS:
            self.skipTest("Segoe UI Semibold is a Windows font")
        if self.theme.semibold_family == self.theme.family:
            self.skipTest("this machine has no Segoe UI Semibold")
        self.assertNotIn("bold", self.theme.font(12, "bold"))

    # ---- what applying it actually did -------------------------------------

    def test_it_uses_the_theme_whose_colours_can_be_set(self):
        """"vista" looks like Windows 7 and cannot be recoloured at all, so
        there would be no dark mode at all if we used it."""
        from tkinter import ttk
        self.assertEqual(ttk.Style(self.root).theme_use(), "clam")

    def test_the_window_itself_is_repainted(self):
        self.assertEqual(str(self.root.cget("background")),
                         self.theme.palette.window)

    def test_the_styles_the_tabs_ask_for_by_name_all_exist(self):
        from tkinter import ttk
        style = ttk.Style(self.root)
        for name in ("Heading.TLabel", "Muted.TLabel", "Big.TLabel",
                     "Verdict.TLabel", "Value.TLabel", "Status.TLabel",
                     "Accent.TButton", "Card.TFrame"):
            with self.subTest(style=name):
                self.assertTrue(style.configure(name),
                                f"{name} was never configured")

    def test_the_accent_button_can_be_read(self):
        """Someone whose Windows accent is bright yellow gets black writing
        on it, not white."""
        from tkinter import ttk
        from cinestat.gui.platform_ui import brightness
        style = ttk.Style(self.root)
        settings = style.configure("Accent.TButton")
        gap = abs(brightness(settings["background"])
                  - brightness(settings["foreground"]))
        self.assertGreater(gap, 90)

    def test_the_tab_strip_stays_level(self):
        """clam gives the selected tab a padding of its own, which drops it
        below its neighbours and reads as a rendering fault."""
        from tkinter import ttk
        selected = dict(ttk.Style(self.root).map("TNotebook.Tab", "padding"))
        self.assertIn("selected", selected)

    # ---- the colour bugs from README.md, guarded ---------------------------

    def test_widget_options_always_set_both_halves_of_a_colour_pair(self):
        """The white-on-white bug: a widget that asks for one colour and
        leaves the other at whatever the system happened to choose."""
        for name, options in (("text", self.theme.text_options()),
                              ("listbox", self.theme.listbox_options()),
                              ("menu", self.theme.menu_options())):
            with self.subTest(widget=name):
                self.assertIn("background", options)
                self.assertIn("foreground", options)

    def test_a_text_box_dressed_by_the_theme_is_readable(self):
        import tkinter as tk
        from cinestat.gui.platform_ui import brightness
        box = tk.Text(self.root, **self.theme.text_options())
        gap = abs(brightness(str(box.cget("background")))
                  - brightness(str(box.cget("foreground"))))
        self.assertGreater(gap, 100)

    def test_menus_do_not_open_with_a_dotted_tear_off_line(self):
        """A Windows menu has never had one; it is a leftover from X11."""
        self.assertEqual(self.theme.menu_options()["tearoff"], 0)

    # ---- tables -----------------------------------------------------------

    def test_striped_rows_alternate(self):
        even, odd = self.theme.STRIPE_TAGS
        self.assertEqual(self.theme.stripe_row(0), even)
        self.assertEqual(self.theme.stripe_row(1), odd)
        self.assertEqual(self.theme.stripe_row(2), even)

    def test_the_two_stripes_are_different_but_barely(self):
        from cinestat.gui.platform_ui import brightness
        gap = abs(brightness(self.theme.palette.surface)
                  - brightness(self.theme.palette.stripe))
        self.assertGreater(gap, 0, "the stripes are identical")
        self.assertLess(gap, 30, "the stripes look like a fault, not a hint")

    def test_preparing_a_table_configures_both_tags(self):
        from tkinter import ttk
        tree = ttk.Treeview(self.root, columns=("a",), show="headings")
        self.theme.prepare_table(tree)
        for tag in self.theme.STRIPE_TAGS:
            with self.subTest(tag=tag):
                self.assertTrue(tree.tag_configure(tag, "background"))

    # ---- charts -----------------------------------------------------------

    def test_every_chart_colour_exists_in_both_looks(self):
        from cinestat.gui.theme import WindowsTheme
        light = set(WindowsTheme.CHART_COLOURS["light"])
        dark = set(WindowsTheme.CHART_COLOURS["dark"])
        self.assertEqual(light, dark)

    def test_the_dark_chart_colours_are_brighter_than_the_light_ones(self):
        """A mid-tone that reads on white paper goes muddy on a dark panel."""
        from cinestat.gui.theme import WindowsTheme
        from cinestat.gui.platform_ui import brightness
        for name in WindowsTheme.CHART_COLOURS["light"]:
            if name == "guide":
                continue                     # a reference line, not a series
            with self.subTest(colour=name):
                self.assertGreater(
                    brightness(WindowsTheme.CHART_COLOURS["dark"][name]),
                    brightness(WindowsTheme.CHART_COLOURS["light"][name]))

    def test_chart_hands_back_the_colour_for_the_current_look(self):
        self.assertEqual(self.theme.chart("green"),
                         self.theme.CHART_COLOURS["dark"]["green"])

    def test_styling_an_axes_recolours_it(self):
        from matplotlib.figure import Figure
        figure = Figure()
        axes = figure.add_subplot(111)
        axes.plot([1, 2, 3], [1, 4, 9], label="something")
        axes.legend()
        self.theme.style_figure(figure)
        self.theme.style_legend(axes)

        self.assertEqual(axes.get_facecolor(),
                         _rgba(self.theme.palette.surface))
        self.assertEqual(figure.get_facecolor(),
                         _rgba(self.theme.palette.surface))
        self.assertEqual(axes.get_legend().get_texts()[0].get_color(),
                         self.theme.palette.text)

    def test_repr_says_which_mode_it_is_in(self):
        self.assertIn("dark", repr(self.theme))


def _rgba(hex_colour):
    """matplotlib answers colours as 0-1 floats, so compare like with like."""
    import matplotlib.colors
    return matplotlib.colors.to_rgba(hex_colour)


if __name__ == "__main__":
    unittest.main()
