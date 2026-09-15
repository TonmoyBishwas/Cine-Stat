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

    def test_all_five_tabs_exist(self):
        self.assertEqual(sorted(self.app.tabs),
                         ["Browse", "Charts", "Compare", "Predict",
                          "Recommend"])

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


    # ---- Recommend tab ----------------------------------------------------

    def _recommend_tab(self, liked=("The Shining", "The Thing", "Aliens")):
        """Reset the tab and tick the given films, as a user would."""
        tab = self.app.tabs["Recommend"]
        tab.clear_liked()
        tab.score_spin.set(0)
        first_year, last_year = self.app.movies.year_bounds()
        tab.year_from.set(first_year)
        tab.year_to.set(last_year)
        for title in liked:
            tab.picker.combo["values"] = [title]
            tab.picker.combo.set(title)
            tab.picker._on_choice()
            tab.add_liked()
        return tab

    def test_ticking_a_film_builds_a_profile(self):
        tab = self._recommend_tab()
        self.assertEqual([m.name for m in tab.liked],
                         ["The Shining", "The Thing", "Aliens"])
        self.assertEqual(tab.liked_list.size(), 3)
        self.assertIn("genres:", tab.profile_label.cget("text"))

    def test_the_same_film_cannot_be_ticked_twice(self):
        tab = self._recommend_tab(liked=["Aliens"])
        tab.add_liked()
        self.assertEqual(len(tab.liked), 1)
        self.assertIn("already on your list", tab.note.cget("text"))

    def test_removing_and_clearing_keep_the_list_and_the_box_in_step(self):
        tab = self._recommend_tab()
        tab.liked_list.selection_set(0)
        tab.remove_liked()
        self.assertEqual(len(tab.liked), tab.liked_list.size())
        self.assertEqual(len(tab.liked), 2)
        tab.clear_liked()
        self.assertEqual(tab.liked_list.size(), 0)

    def test_every_method_produces_suggestions(self):
        """POLYMORPHISM in the GUI: one button, three different classes."""
        tab = self._recommend_tab()
        for method in tab.ENGINES:
            with self.subTest(method=method):
                tab.engine_box.set(method)
                tab.recommend()
                self.assertEqual(len(tab.results), tab.HOW_MANY)
                self.assertEqual(len(tab.tree.get_children()), len(tab.results))
                scores = [r.score for r in tab.results]
                self.assertEqual(scores, sorted(scores, reverse=True))

    def test_a_film_the_user_ticked_is_never_suggested(self):
        tab = self._recommend_tab()
        for method in tab.ENGINES:
            with self.subTest(method=method):
                tab.engine_box.set(method)
                tab.recommend()
                suggested = [r.movie.name for r in tab.results]
                for movie in tab.liked:
                    self.assertNotIn(movie.name, suggested)

    def test_the_reasons_appear_without_the_user_clicking_anything(self):
        tab = self._recommend_tab()
        tab.engine_box.set("Matches my taste")
        tab.recommend()
        shown = tab.explanation.get("1.0", "end")
        self.assertIn(tab.results[0].movie.name, shown)
        self.assertIn("Why you might like it", shown)

    def test_clicking_a_row_explains_that_row(self):
        tab = self._recommend_tab()
        tab.recommend()
        rows = tab.tree.get_children()
        tab.tree.selection_set(rows[2])
        tab.show_reasons()
        self.assertIn(tab.results[2].movie.name,
                      tab.explanation.get("1.0", "end"))

    def test_the_settings_narrow_the_suggestions(self):
        tab = self._recommend_tab()
        tab.score_spin.set(8.0)
        tab.year_from.set(2000)
        tab.year_to.set(2010)
        tab.recommend()
        self.assertTrue(tab.results)
        for recommendation in tab.results:
            movie = recommendation.movie
            self.assertGreaterEqual(movie.score, 8.0)
            self.assertTrue(2000 <= movie.year <= 2010)

    def test_a_backwards_year_range_shows_a_dialog_and_does_not_crash(self):
        """Class 9: the custom exception reaches the user as a message box."""
        from cinestat.gui import recommend_tab as module

        tab = self._recommend_tab()
        shown = []
        original = module.messagebox.showerror
        module.messagebox.showerror = lambda title, message, **kw: \
            shown.append(message)
        try:
            tab.year_from.set(2010)
            tab.year_to.set(1990)
            tab.recommend()
            self.assertEqual(len(shown), 1)
            self.assertTrue(self.app.winfo_exists())
        finally:
            module.messagebox.showerror = original

    def test_similar_needs_a_film_and_says_so_politely(self):
        from cinestat.gui import recommend_tab as module

        tab = self._recommend_tab(liked=[])
        shown = []
        original = module.messagebox.showinfo
        module.messagebox.showinfo = lambda title, message, **kw: \
            shown.append(message)
        try:
            tab.engine_box.set("Similar to my last pick")
            tab.recommend()
            self.assertEqual(len(shown), 1)
        finally:
            module.messagebox.showinfo = original

    # ---- the AI explanation, without touching the internet ----------------

    def _run_ai_worker_with(self, fake_explainer_class, timeout=10):
        """Press the real button with a fake explainer behind it.

        This drives the WHOLE path - the real background thread, the queue
        between the threads, and the main thread's polling - because that
        handoff is where the bugs live. Calling _ai_worker() directly instead
        would skip all of it, and did: an earlier version of this helper did
        exactly that and missed a bug that left the button disabled forever.
        No network is touched; the fake explainer answers instantly.
        """
        import time
        from cinestat.gui import recommend_tab as module

        tab = self._recommend_tab()
        tab.recommend()
        self.app.notebook.select(tab)

        original = module.AIExplainer
        module.AIExplainer = fake_explainer_class
        try:
            tab.explain_with_ai()
            # The button must go dead the instant it is pressed, or an
            # impatient user fires a second request on top of the first.
            self.assertEqual(str(tab.ai_button.cget("state")), "disabled")

            deadline = time.time() + timeout
            while tab._ai_busy and time.time() < deadline:
                self.app.update()
                time.sleep(0.01)
            self.assertFalse(tab._ai_busy,
                             "the reply never reached the main thread")
        finally:
            module.AIExplainer = original
        return tab

    def test_a_successful_ai_call_replaces_the_explanation(self):
        class FakeAI:
            model = "test/model"
            last_error = None
            def explain_or_fallback(self, recommendation, preference):
                return "The AI wrote this sentence."

        tab = self._run_ai_worker_with(FakeAI)
        self.assertIn("The AI wrote this sentence.",
                      tab.explanation.get("1.0", "end"))
        self.assertIn("test/model", tab.note.cget("text"))
        self.assertFalse(tab._ai_busy)
        self.assertEqual(str(tab.ai_button.cget("state")), "normal")

    def test_a_failed_ai_call_falls_back_and_says_why(self):
        """The demo must survive a missing key or a dead wifi connection."""
        class BrokenAI:
            model = "test/model"
            last_error = "Could not reach OpenRouter: no internet"
            def explain_or_fallback(self, recommendation, preference):
                return "Built-in reasons instead."

        tab = self._run_ai_worker_with(BrokenAI)
        shown = tab.explanation.get("1.0", "end")
        self.assertIn("Built-in reasons instead.", shown)
        self.assertIn("no internet", shown)
        self.assertIn("AI unavailable", tab.note.cget("text"))
        self.assertEqual(str(tab.ai_button.cget("state")), "normal")

    def test_nothing_is_squeezed_off_the_recommend_tab(self):
        """Regression: the settings, the film list and the profile line used
        to be stacked in one column that needed 578 pixels of height in a
        column that only has 435 at the smallest allowed window size. Tkinter
        does not complain - it silently shrinks the last widgets to 1x1."""
        tab = self._recommend_tab()
        tab.recommend()
        self.app.notebook.select(tab)

        original = self.app.geometry()
        try:
            for size in ("950x640", "1150x740"):
                self.app.geometry(size)
                self.app.update()
                widgets = {
                    "film picker": tab.picker,
                    "liked list": tab.liked_list,
                    "method dropdown": tab.engine_box,
                    "minimum IMDb": tab.score_spin,
                    "year to": tab.year_to,
                    "profile line": tab.profile_label,
                    "results table": tab.tree,
                    "explain button": tab.ai_button,
                    "explanation box": tab.explanation,
                }
                for name, widget in widgets.items():
                    with self.subTest(size=size, widget=name):
                        left = widget.winfo_rootx() - self.app.winfo_rootx()
                        top = widget.winfo_rooty() - self.app.winfo_rooty()
                        self.assertGreater(widget.winfo_width(), 30,
                                           f"{name} was squeezed flat")
                        self.assertGreater(widget.winfo_height(), 8,
                                           f"{name} was squeezed flat")
                        self.assertLessEqual(
                            left + widget.winfo_width(),
                            self.app.winfo_width() + 2,
                            f"{name} runs off the right edge")
                        self.assertLessEqual(
                            top + widget.winfo_height(),
                            self.app.winfo_height() + 2,
                            f"{name} runs off the bottom edge")
        finally:
            self.app.geometry(original)
            self.app.update()

    def test_an_explainer_that_crashes_still_gives_the_button_back(self):
        """If the worker thread dies quietly the button stays greyed out and
        the tab is dead until the program is restarted."""
        class ExplodingAI:
            def __init__(self):
                raise RuntimeError("something went badly wrong")

        tab = self._run_ai_worker_with(ExplodingAI)
        shown = tab.explanation.get("1.0", "end")
        self.assertIn("Why you might like it", shown)      # offline fallback
        self.assertIn("something went badly wrong", shown)
        self.assertFalse(tab._ai_busy)
        self.assertEqual(str(tab.ai_button.cget("state")), "normal")

    def test_the_explanation_is_actually_readable(self):
        """Regression: the box asked for a near-white background and left the
        text colour alone. In macOS dark mode the text colour is WHITE, so
        the explanation was white on white - invisible. A test that only
        checks the words are present passes happily while the user sees a
        blank box, so this one compares the two colours."""
        tab = self._recommend_tab()
        tab.recommend()

        box = tab.explanation
        background = box.winfo_rgb(box.cget("background"))
        text = box.winfo_rgb(box.cget("foreground"))
        # winfo_rgb answers 0-65535 per channel; scale back to 0-255.
        gap = abs(sum(background) / 3 - sum(text) / 3) / 257
        self.assertGreater(gap, 80,
                           f"explanation text is invisible: background "
                           f"{background} against text {text}")

    def test_secondary_labels_contrast_with_the_window(self):
        """Same bug, one shade milder: '#555555' vanishes on a dark window."""
        from cinestat.gui.base_tab import muted_colour

        tab = self._recommend_tab()
        window = tab.winfo_rgb(tab.winfo_toplevel().cget("background"))
        for name, widget in (("profile line", tab.profile_label),
                             ("status note", tab.note)):
            with self.subTest(label=name):
                colour = tab.winfo_rgb(widget.cget("foreground"))
                gap = abs(sum(window) / 3 - sum(colour) / 3) / 257
                self.assertGreater(gap, 40,
                                   f"{name} does not contrast with the window")

        self.assertIn(muted_colour(tab), ("#9A9A9A", "#555555"))

    def test_the_user_can_see_that_the_ai_is_working(self):
        """Regression: a reasoning model takes 5-10 seconds and the window
        showed nothing at all, which is indistinguishable from a crash."""
        import time
        from cinestat.gui import recommend_tab as module

        seen = {}

        class SlowAI:
            model = "test/model"
            last_error = None
            def explain_or_fallback(self, recommendation, preference):
                time.sleep(0.9)          # long enough for the UI to tick
                return "Finished at last."

        tab = self._recommend_tab()
        tab.recommend()
        original = module.AIExplainer
        original_tick = tab.TICK_MILLISECONDS
        module.AIExplainer = SlowAI
        # Tick faster than the real 300 ms, so the counter is guaranteed to
        # move several times inside the fake's 0.9 s. Left at 300 this test
        # passed four runs out of five, which is worse than no test at all.
        tab.TICK_MILLISECONDS = 50
        try:
            tab.explain_with_ai()
            # Straight away: the button says what it is doing, the bar shows.
            self.assertEqual(tab.ai_button.cget("text"), "Asking the AI...")
            self.assertEqual(str(tab.ai_button.cget("state")), "disabled")
            self.assertTrue(tab.progress.winfo_manager(),
                            "the progress bar is not on screen")
            self.assertIn("Asking the AI",
                          tab.explanation.get("1.0", "end"))

            deadline = time.time() + 15
            while tab._ai_busy and time.time() < deadline:
                self.app.update()
                seen[tab.note.cget("text")] = True
                time.sleep(0.01)
        finally:
            module.AIExplainer = original
            tab.TICK_MILLISECONDS = original_tick

        # The counter must actually have moved, not just sat there.
        waiting = [note for note in seen if note.startswith("Waiting for the AI")]
        self.assertGreater(len(waiting), 1,
                           f"the waiting message never changed: {list(seen)}")

        # And everything must be put back afterwards.
        self.assertFalse(tab.progress.winfo_manager(),
                         "the progress bar was left on screen")
        self.assertEqual(tab.ai_button.cget("text"), "Explain with AI")
        self.assertEqual(str(tab.ai_button.cget("state")), "normal")
        self.assertIn("Finished at last.", tab.explanation.get("1.0", "end"))

    # ---- exporting from whichever tab is open -----------------------------

    def test_export_follows_the_tab_that_is_open(self):
        recommend = self._recommend_tab()
        recommend.recommend()
        self.app.notebook.select(recommend)
        self.assertIs(self.app.active_tab(), recommend)

        rows = self.app.active_tab().current_rows()
        self.assertEqual(len(rows), len(recommend.results))
        self.assertIn("match_score", rows[0])
        self.assertIn("reasons", rows[0])

        self.app.notebook.select(self.app.tabs["Browse"])
        self.assertIs(self.app.active_tab(), self.app.tabs["Browse"])

    def test_a_tab_with_nothing_to_export_falls_back_to_browse(self):
        self.app.notebook.select(self.app.tabs["Charts"])
        self.assertIs(self.app.active_tab(), self.app.tabs["Browse"])
        self.app.notebook.select(self.app.tabs["Browse"])

    # ---- File menu export -------------------------------------------------

    def test_export_writes_exactly_the_filtered_rows(self):
        from cinestat.gui import app as app_module

        browse = self.app.tabs["Browse"]
        self.app.notebook.select(browse)      # export follows the open tab
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
