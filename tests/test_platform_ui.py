"""Tests for the Windows integration layer.

Almost nothing in here needs a window, because `platform_ui` is the file that
talks to the operating system rather than to Tk. What it mostly needs to prove
is that every one of those conversations is allowed to fail: the same source
has to run on a Mac, on Linux, and on a Windows old enough not to have the
registry keys we read - and in every one of those cases it has to come back
with a sensible answer instead of an exception.
"""

import os
import unittest

from cinestat.gui import platform_ui


class TestKeyboardShortcuts(unittest.TestCase):
    """The menu's promise and the actual binding come from one function.

    This matters more than it looks: Tk binds nothing at all if the letter in
    the sequence is the wrong case, and it does it silently, so the menu can
    end up advertising a shortcut that does nothing whatsoever.
    """

    def test_a_plain_shortcut(self):
        label, sequence = platform_ui.shortcut("e")
        self.assertEqual(label, f"{platform_ui.MODIFIER_LABEL}+E")
        self.assertEqual(sequence, f"<{platform_ui.MODIFIER_KEY}-e>")

    def test_a_shift_shortcut_uses_a_capital_letter(self):
        """With Shift, Tk wants the capital; without it, the lower case."""
        label, sequence = platform_ui.shortcut("e", shift=True)
        self.assertIn("Shift", label)
        self.assertTrue(label.endswith("+E"))
        self.assertTrue(sequence.endswith("-Shift-E>"))

    def test_a_number_shortcut(self):
        label, sequence = platform_ui.shortcut("3")
        self.assertTrue(label.endswith("+3"))
        self.assertTrue(sequence.endswith("-3>"))

    def test_windows_uses_control_and_a_mac_uses_command(self):
        if platform_ui.IS_MACOS:
            self.assertEqual(platform_ui.MODIFIER_KEY, "Command")
        else:
            self.assertEqual(platform_ui.MODIFIER_KEY, "Control")


class TestColourArithmetic(unittest.TestCase):
    """Deciding whether black or white can be read on a given colour."""

    def test_brightness_of_the_two_extremes(self):
        self.assertEqual(platform_ui.brightness("#000000"), 0)
        self.assertEqual(round(platform_ui.brightness("#FFFFFF")), 255)

    def test_green_counts_for_more_than_blue(self):
        """Which is why a yellow accent needs black writing and a navy one
        needs white, even though both are 'one bright channel'."""
        self.assertGreater(platform_ui.brightness("#00FF00"),
                           platform_ui.brightness("#0000FF"))

    def test_readable_text_colour(self):
        self.assertEqual(platform_ui.readable_on("#FFFF00"), "#000000")
        self.assertEqual(platform_ui.readable_on("#0B5FA5"), "#FFFFFF")

    def test_nonsense_does_not_raise(self):
        self.assertEqual(platform_ui.brightness("not a colour"), 255)


class TestTheSystemTheme(unittest.TestCase):
    """Reading 'is Windows in dark mode?' out of the registry."""

    def setUp(self):
        self._saved = os.environ.get(platform_ui.THEME_VARIABLE)

    def tearDown(self):
        os.environ.pop(platform_ui.THEME_VARIABLE, None)
        if self._saved is not None:
            os.environ[platform_ui.THEME_VARIABLE] = self._saved

    def test_it_is_always_one_of_two_answers(self):
        os.environ.pop(platform_ui.THEME_VARIABLE, None)
        self.assertIn(platform_ui.system_theme(), ("light", "dark"))

    def test_the_environment_variable_wins(self):
        """So the other look can be checked without changing the whole
        computer's settings:  set CINESTAT_THEME=light"""
        for wanted in ("light", "dark"):
            os.environ[platform_ui.THEME_VARIABLE] = wanted
            self.assertEqual(platform_ui.system_theme(), wanted)

    def test_a_silly_value_is_ignored(self):
        os.environ[platform_ui.THEME_VARIABLE] = "purple"
        self.assertIn(platform_ui.system_theme(), ("light", "dark"))

    def test_capitals_and_spaces_are_forgiven(self):
        os.environ[platform_ui.THEME_VARIABLE] = "  DARK "
        self.assertEqual(platform_ui.system_theme(), "dark")


class TestScreenScale(unittest.TestCase):
    """How much bigger everything has to be drawn on a high-DPI screen."""

    def setUp(self):
        self._saved = os.environ.get(platform_ui.SCALE_VARIABLE)

    def tearDown(self):
        os.environ.pop(platform_ui.SCALE_VARIABLE, None)
        if self._saved is not None:
            os.environ[platform_ui.SCALE_VARIABLE] = self._saved

    def test_it_is_a_sensible_number_with_no_window(self):
        os.environ.pop(platform_ui.SCALE_VARIABLE, None)
        scale = platform_ui.screen_scale(None)
        self.assertGreaterEqual(scale, 1.0)
        self.assertLessEqual(scale, 4.0)

    def test_the_environment_variable_wins(self):
        os.environ[platform_ui.SCALE_VARIABLE] = "1.5"
        self.assertEqual(platform_ui.screen_scale(None), 1.5)

    def test_it_refuses_to_go_below_one_or_beyond_four(self):
        os.environ[platform_ui.SCALE_VARIABLE] = "0.1"
        self.assertEqual(platform_ui.screen_scale(None), 1.0)
        os.environ[platform_ui.SCALE_VARIABLE] = "99"
        self.assertEqual(platform_ui.screen_scale(None), 4.0)

    def test_nonsense_falls_back_to_asking_windows(self):
        os.environ[platform_ui.SCALE_VARIABLE] = "very big please"
        self.assertGreaterEqual(platform_ui.screen_scale(None), 1.0)


class TestTalkingToWindows(unittest.TestCase):
    """Every one of these is allowed to fail, and none may raise."""

    def test_preparing_the_process_answers_yes_or_no(self):
        self.assertIsInstance(platform_ui.prepare_process(), bool)

    def test_claiming_dpi_awareness_answers_yes_or_no(self):
        self.assertIsInstance(platform_ui.set_dpi_awareness(), bool)

    def test_claiming_a_taskbar_button_answers_yes_or_no(self):
        self.assertIsInstance(platform_ui.set_app_user_model_id(), bool)

    def test_the_accent_colour_is_a_colour_or_nothing(self):
        accent = platform_ui.accent_colour()
        if accent is not None:
            self.assertRegex(accent, r"^#[0-9A-F]{6}$")

    def test_a_dark_titlebar_is_only_attempted_on_windows(self):
        """Nothing to call DwmSetWindowAttribute on anywhere else."""
        if not platform_ui.IS_WINDOWS:
            self.assertFalse(platform_ui.use_dark_titlebar(None))


class TestTheIcon(unittest.TestCase):
    """The icon is committed to the repository, not built on the fly."""

    def test_both_icon_files_are_there(self):
        self.assertTrue(platform_ui.ICON_ICO.exists(),
                        "assets/cinestat.ico is missing - run tools/make_icon.py")
        self.assertTrue(platform_ui.ICON_PNG.exists(),
                        "assets/cinestat.png is missing - run tools/make_icon.py")

    def test_the_ico_really_is_an_ico(self):
        """The first six bytes are reserved=0, type=1 (icon), and a count."""
        import struct
        header = platform_ui.ICON_ICO.read_bytes()[:6]
        reserved, kind, count = struct.unpack("<HHH", header)
        self.assertEqual(reserved, 0)
        self.assertEqual(kind, 1)
        self.assertGreaterEqual(count, 1)

    def test_it_holds_the_sizes_windows_asks_for(self):
        """16 for a file list, 32 for the taskbar, 256 for the preview pane."""
        import struct
        data = platform_ui.ICON_ICO.read_bytes()
        _, _, count = struct.unpack("<HHH", data[:6])
        sizes = set()
        for index in range(count):
            start = 6 + 16 * index
            width = data[start]
            sizes.add(256 if width == 0 else width)
        for wanted in (16, 32, 256):
            self.assertIn(wanted, sizes)


if __name__ == "__main__":
    unittest.main()
