"""Tests for the Tkinter application.

These build the real window but never call mainloop(), so they run and finish
on their own. If the computer has no screen available (for example on a server)
every test here is skipped instead of failing.
"""

import csv
import json
import tempfile
import unittest
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "movies.csv"


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


@unittest.skipUnless(HAVE_SCREEN, "no screen available")
@unittest.skipUnless(DATA_FILE.exists(), "data/movies.csv not downloaded")
class TestApplication(unittest.TestCase):
    """One window is built for the whole class, because loading takes a moment."""

    @classmethod
    def setUpClass(cls):
        from cinestat.gui.app import MovieApp
        cls.app = MovieApp(DATA_FILE)
        cls.app.withdraw()          # build it, but keep it off the screen

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    # ---- the window itself ------------------------------------------------

    def test_all_four_tabs_exist(self):
        self.assertEqual(sorted(self.app.tabs),
                         ["Browse", "Charts", "Compare", "Predict"])

    def test_data_and_model_are_ready(self):
        self.assertGreater(len(self.app.movies), 5000)
        self.assertTrue(self.app.predictor.is_trained)

    def test_tabs_do_not_override_str(self):
        """Tkinter uses str(widget) as the widget's path name.

        Overriding __str__ on a widget subclass breaks notebook.add(), so this
        test guards against someone adding one back by mistake.
        """
        for tab in self.app.tabs.values():
            self.assertTrue(str(tab).startswith("."),
                            f"{type(tab).__name__} broke its Tkinter path name")

    # ---- Browse tab -------------------------------------------------------

    def test_browse_starts_with_every_film(self):
        browse = self.app.tabs["Browse"]
        browse.reset_filters()
        self.assertEqual(len(browse.rows), len(self.app.movies))

    def test_browse_filters_narrow_the_list(self):
        browse = self.app.tabs["Browse"]
        browse.reset_filters()
        everything = len(browse.rows)

        browse.genre_box.set("Horror")
        browse.year_from.set(1980)
        browse.year_to.set(1990)
        browse.apply_filters()

        self.assertLess(len(browse.rows), everything)
        self.assertTrue(all(m.genre == "Horror" for m in browse.rows))
        self.assertTrue(all(1980 <= m.year <= 1990 for m in browse.rows))
        self.assertEqual(len(browse.tree.get_children()), len(browse.rows))
        browse.reset_filters()

    def test_browse_sorting_toggles_direction(self):
        browse = self.app.tabs["Browse"]
        browse.reset_filters()

        browse.sort_by("gross")
        ascending = [m.gross for m in browse.rows]
        self.assertEqual(ascending, sorted(ascending))

        browse.sort_by("gross")
        descending = [m.gross for m in browse.rows]
        self.assertEqual(descending, sorted(descending, reverse=True))

    # ---- Charts tab -------------------------------------------------------

    def test_every_chart_draws_without_error(self):
        charts = self.app.tabs["Charts"]
        self.assertEqual(len(charts.charts), 8)
        for name in charts.charts:
            with self.subTest(chart=name):
                charts.chooser.set(name)
                charts.draw()
                self.assertTrue(charts.figure.axes)

    # ---- Compare tab ------------------------------------------------------

    def test_compare_uses_the_greater_than_operator(self):
        compare = self.app.tabs["Compare"]
        avatar = self.app.movies.find("Avatar")
        titanic = self.app.movies.find("Titanic")

        compare.left.combo["values"] = ["Avatar"]
        compare.left.combo.set("Avatar")
        compare.left._on_choice()
        compare.right.combo["values"] = ["Titanic"]
        compare.right.combo.set("Titanic")
        compare.right._on_choice()

        winner = avatar if avatar > titanic else titanic
        self.assertIn(winner.name, compare.verdict.cget("text"))
        self.assertEqual(len(compare.table.get_children()), len(compare.FIELDS))

    # ---- Predict tab ------------------------------------------------------

    def _fill_prediction_form(self, budget):
        predict = self.app.tabs["Predict"]
        predict.budget_entry.delete(0, "end")
        predict.budget_entry.insert(0, str(budget))
        predict.genre_box.set("Action")
        predict.rating_box.set("PG-13")
        predict.runtime_spin.set(120)
        predict.month_box.set("July")
        return predict

    def test_valid_input_shows_a_prediction(self):
        predict = self._fill_prediction_form(50_000_000)
        predict.predict()
        self.assertIn("$", predict.gross_label.cget("text"))
        self.assertIn(predict.verdict_label.cget("text"),
                      ("Hit", "Break-even", "Flop"))

    def test_bad_budget_shows_a_message_box_and_does_not_crash(self):
        """Class 9: the custom exception reaches the user as a dialog."""
        from cinestat.gui import predict_tab

        shown = []
        original = predict_tab.messagebox.showerror
        predict_tab.messagebox.showerror = lambda title, message, **kw: \
            shown.append(message)
        try:
            for bad_value in (-5, 0, "fifty million"):
                with self.subTest(budget=bad_value):
                    shown.clear()
                    self._fill_prediction_form(bad_value).predict()
                    self.assertEqual(len(shown), 1)
            self.assertTrue(self.app.winfo_exists())
        finally:
            predict_tab.messagebox.showerror = original

    # ---- File menu export -------------------------------------------------

    def test_export_writes_exactly_the_filtered_rows(self):
        from cinestat.gui import app as app_module

        browse = self.app.tabs["Browse"]
        browse.reset_filters()
        browse.genre_box.set("Horror")
        browse.apply_filters()
        expected = len(browse.rows)

        original_dialog = app_module.filedialog.asksaveasfilename
        original_info = app_module.messagebox.showinfo
        app_module.messagebox.showinfo = lambda *a, **k: None
        try:
            with tempfile.TemporaryDirectory() as folder:
                for file_format in ("csv", "json"):
                    with self.subTest(format=file_format):
                        target = Path(folder) / f"out.{file_format}"
                        app_module.filedialog.asksaveasfilename = \
                            (lambda p: (lambda **kw: p))(str(target))
                        self.app.export(file_format)

                        if file_format == "csv":
                            rows = list(csv.DictReader(
                                target.read_text().splitlines()))
                        else:
                            rows = json.loads(target.read_text())

                        self.assertEqual(len(rows), expected)
                        self.assertTrue(all(r["genre"] == "Horror" for r in rows))
        finally:
            app_module.filedialog.asksaveasfilename = original_dialog
            app_module.messagebox.showinfo = original_info
            browse.reset_filters()


if __name__ == "__main__":
    unittest.main()
