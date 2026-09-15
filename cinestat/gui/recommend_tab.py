"""Recommend tab - "tick films you liked, and we will suggest more".

How it works, in four steps:

  1. The user picks films they enjoyed. They go into a list on the left.
  2. `UserPreference.from_movies()` turns that list into a taste profile.
  3. One of the three recommenders scores every other film against it.
  4. The reasons appear instantly. Pressing "Explain with AI" sends those
     same reasons to OpenRouter and replaces them with a nicer paragraph.

Syllabus topics demonstrated here:
  Class 7  - widgets, layout managers, callbacks, our own MoviePicker reused
  Class 8  - MVC-lite: this file decides nothing. It asks the classes in
             cinestat/ for the answers and only draws them.
  Class 9  - custom exceptions surfaced to the user as a message
  Class 12 - MULTITHREADING: the AI call runs on a background thread, so the
             window never freezes while we wait for the internet.
"""

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from .base_tab import BaseTab, muted_colour
from .widgets import MoviePicker
from ..preferences import UserPreference
from ..recommenders import (ContentRecommender, SimilarityRecommender,
                            PopularityRecommender)
from ..explainers import RuleExplainer, AIExplainer
from ..utils import ExportSession
from ..exceptions import MovieDataError


class RecommendTab(BaseTab):
    """Suggests films based on the ones the user says they like."""

    title = "Recommend"

    # Class 11 again: a dictionary mapping a name to the CLASS that provides
    # it. Adding a fourth recommender means adding one name to this list and
    # nothing else. The dropdown labels are taken from each class's own
    # `title`, so the menu and the code can never disagree.
    ENGINE_CLASSES = [ContentRecommender, SimilarityRecommender,
                      PopularityRecommender]
    ENGINES = {engine.title: engine for engine in ENGINE_CLASSES}

    HOW_MANY = 15

    COLUMNS = [
        ("match", "Match", 70),
        ("name", "Title", 250),
        ("year", "Year", 55),
        ("genre", "Genre", 100),
        ("rating", "Rating", 75),
        ("score", "IMDb", 55),
        ("runtime", "Runtime", 75),
    ]

    # ---- building the tab -------------------------------------------------

    def build_ui(self):
        # These must exist before any callback can possibly fire.
        self.liked = []                  # the Movie objects the user ticked
        self.results = []                # the current list of Recommendations
        self.preference = UserPreference()
        self.rule_explainer = RuleExplainer()
        self._ai_busy = False
        self._ai_started = None         # when the current request was sent
        # The letterbox between the two threads. A Queue is safe to use from
        # any thread, unlike a Tkinter widget - see explain_with_ai below.
        self._ai_replies = queue.Queue()

        self.add_heading(
            "Find me something to watch",
            "Add a few films you enjoyed. CineStat works out what they have "
            "in common, scores every other film against that, and shows you "
            "why each suggestion was made.")

        # The settings go in a wide strip of their own. Stacked in the left
        # column they needed 578 pixels of height in a column that only has
        # 435 at the smallest allowed window size, and the film list got
        # squeezed down to nothing.
        self._build_settings(self)

        columns = ttk.Frame(self)
        columns.pack(fill="both", expand=True, pady=(10, 0))
        columns.columnconfigure(0, weight=0)
        columns.columnconfigure(1, weight=1)
        columns.rowconfigure(0, weight=1)

        self._build_left_panel(columns)
        self._build_right_panel(columns)
        self._refresh_profile_label()

    # ---- left: choosing the films you like --------------------------------

    def _build_left_panel(self, parent):
        panel = ttk.Frame(parent)
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        # Reusing the custom widget the Compare tab already uses. Writing it
        # as its own class is what makes this one line possible.
        self.picker = MoviePicker(panel, self.movies, label="Films I liked")
        self.picker.pack(fill="x")

        ttk.Button(panel, text="Add this film to my list",
                   command=self.add_liked).pack(fill="x", pady=(8, 10))

        # Everything that must always be visible is packed to the BOTTOM
        # first. pack() hands out space in the order it is asked, so doing it
        # this way reserves room for the button and the profile line before
        # the films list gets a chance to swallow it. Pack the list first and
        # its expand=True eats the lot, pushing the profile line off the
        # screen on a smaller window - which is exactly what happened.
        self.profile_label = ttk.Label(panel, text="", wraplength=300,
                                       justify="left",
                                       foreground=muted_colour(self))
        self.profile_label.pack(side="bottom", anchor="w", pady=(6, 0))

        ttk.Button(panel, text="Recommend films for me",
                   command=self.recommend).pack(side="bottom", fill="x",
                                                pady=(12, 0))

        # Packed last, so it expands into whatever height is left over.
        box = ttk.LabelFrame(panel, text="My films", padding=8)
        box.pack(side="top", fill="both", expand=True)

        self.liked_list = tk.Listbox(box, height=5, exportselection=False,
                                     activestyle="none")
        self.liked_list.pack(fill="both", expand=True)

        buttons = ttk.Frame(box)
        buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(buttons, text="Remove",
                   command=self.remove_liked).pack(side="left", expand=True,
                                                   fill="x", padx=(0, 4))
        ttk.Button(buttons, text="Clear all",
                   command=self.clear_liked).pack(side="left", expand=True,
                                                  fill="x", padx=(4, 0))

    def _build_settings(self, parent):
        """One horizontal strip: how to recommend, and what to leave out."""
        box = ttk.LabelFrame(parent, text="Settings", padding=(10, 8))
        box.pack(fill="x")

        first_year, last_year = self.movies.year_bounds()

        ttk.Label(box, text="Method:").pack(side="left")
        self.engine_box = ttk.Combobox(box, state="readonly", width=24,
                                       values=list(self.ENGINES))
        self.engine_box.current(0)
        self.engine_box.pack(side="left", padx=(5, 20))

        ttk.Label(box, text="Minimum IMDb:").pack(side="left")
        self.score_spin = ttk.Spinbox(box, from_=0, to=10, increment=0.5,
                                      width=5)
        self.score_spin.set(0)
        self.score_spin.pack(side="left", padx=(5, 20))

        ttk.Label(box, text="Years:").pack(side="left")
        self.year_from = ttk.Spinbox(box, from_=first_year, to=last_year,
                                     width=6)
        self.year_from.set(first_year)
        self.year_from.pack(side="left", padx=(5, 2))
        ttk.Label(box, text="to").pack(side="left")
        self.year_to = ttk.Spinbox(box, from_=first_year, to=last_year, width=6)
        self.year_to.set(last_year)
        self.year_to.pack(side="left", padx=(2, 0))

    # ---- right: the results and the explanation ---------------------------

    def _build_right_panel(self, parent):
        panel = ttk.Frame(parent)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.rowconfigure(0, weight=3)
        panel.rowconfigure(2, weight=2)
        panel.columnconfigure(0, weight=1)

        table_frame = ttk.Frame(panel)
        table_frame.grid(row=0, column=0, sticky="nsew")

        self.tree = ttk.Treeview(table_frame,
                                 columns=[key for key, _, _ in self.COLUMNS],
                                 show="headings", selectmode="browse")
        for key, heading, width in self.COLUMNS:
            self.tree.heading(key, text=heading)
            anchor = "w" if key in ("name", "genre", "rating") else "e"
            self.tree.column(key, width=width, anchor=anchor,
                             stretch=(key == "name"))
        # Clicking a row shows the reasons for that film straight away.
        self.tree.bind("<<TreeviewSelect>>", self.show_reasons)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        controls = ttk.Frame(panel)
        controls.grid(row=1, column=0, sticky="ew", pady=(10, 4))
        self.ai_button = ttk.Button(controls, text="Explain with AI",
                                    command=self.explain_with_ai,
                                    state="disabled")
        self.ai_button.pack(side="left")
        self.export_button = ttk.Button(controls, text="Save these as CSV...",
                                        command=self.export_results,
                                        state="disabled")
        self.export_button.pack(side="left", padx=(8, 0))

        # A barber-pole bar that only appears while we are waiting for the
        # AI. Built now, but not packed - it is shown and hidden by
        # explain_with_ai() and _show_ai_result().
        self.progress = ttk.Progressbar(controls, mode="indeterminate",
                                        length=130)

        self.note = ttk.Label(controls, text="",
                              foreground=muted_colour(self), wraplength=380)
        self.note.pack(side="left", padx=(12, 0))

        explain_box = ttk.LabelFrame(panel, text="Why this film?", padding=8)
        explain_box.grid(row=2, column=0, sticky="nsew")

        # No hard-coded colours. This widget used to ask for a near-white
        # background while leaving the text colour alone - and in macOS dark
        # mode the text colour is WHITE, so the explanation was white on
        # white and completely invisible. Left alone, Tkinter uses the same
        # system colours as the Listbox above, which are correct in both
        # light mode and dark mode.
        self.explanation = tk.Text(explain_box, height=9, wrap="word",
                                   relief="flat", padx=8, pady=6)
        text_scroll = ttk.Scrollbar(explain_box, orient="vertical",
                                    command=self.explanation.yview)
        self.explanation.configure(yscrollcommand=text_scroll.set)
        self.explanation.pack(side="left", fill="both", expand=True)
        text_scroll.pack(side="right", fill="y")
        self._write_explanation(
            "Add a film or two on the left, then press "
            "\"Recommend films for me\".")

    # ---- callbacks: managing the liked list -------------------------------

    def add_liked(self):
        """Put the film currently in the picker into the user's list."""
        movie = self.picker.selected
        if movie is None:
            return
        if movie in self.liked:
            self._set_note(f"{movie.name} is already on your list.")
            return
        self.liked.append(movie)
        self.liked_list.insert("end", f"{movie.name} ({movie.year})")
        self._refresh_profile_label()
        self._set_note("")

    def remove_liked(self):
        """Take the highlighted film back off the list."""
        chosen = self.liked_list.curselection()
        if not chosen:
            return
        index = chosen[0]
        self.liked_list.delete(index)
        del self.liked[index]
        self._refresh_profile_label()

    def clear_liked(self):
        """Empty the list completely."""
        self.liked.clear()
        self.liked_list.delete(0, "end")
        self._refresh_profile_label()

    # ---- callback: the actual recommendation ------------------------------

    def build_preference(self):
        """Turn the ticked films plus the settings into a UserPreference.

        All the thinking happens inside UserPreference and the recommenders.
        This method only collects what the user typed.
        """
        preference = UserPreference.from_movies(self.liked)
        try:
            # from_movies() already worked out a sensible floor from the films
            # that were ticked. The spinbox can RAISE that floor but must not
            # quietly erase it, or the profile shown on screen would be a lie.
            preference.min_score = max(preference.min_score,
                                       float(self.score_spin.get()))
            preference.year_from = int(self.year_from.get())
            preference.year_to = int(self.year_to.get())
        except ValueError:
            raise MovieDataError(
                "Please check the minimum IMDb score and the year range - "
                "they must be numbers.")
        if preference.year_from > preference.year_to:
            raise MovieDataError("The 'from' year must not be after the 'to' year.")
        return preference

    def recommend(self):
        """Read the form, run the chosen recommender, show the results."""
        try:
            self.preference = self.build_preference()
        except MovieDataError as error:
            messagebox.showerror("Cannot recommend", str(error))
            return

        engine_class = self.ENGINES[self.engine_box.get()]
        # POLYMORPHISM: we do not know or care which of the three classes this
        # is. Every one of them answers .recommend() the same way.
        engine = engine_class(self.movies, self.preference)

        if isinstance(engine, SimilarityRecommender) and engine.seed is None:
            messagebox.showinfo(
                "Pick a film first",
                "\"Similar to my last pick\" needs at least one film on your "
                "list, because it compares everything against that film.")
            return

        self.results = engine.recommend(self.HOW_MANY)
        self._refresh_table()

        if not self.results:
            self._set_note("Nothing matched. Try widening the years or "
                           "lowering the minimum IMDb score.")
            self._write_explanation("No films matched your settings.")
            return

        self._set_note(f"{len(self.results)} suggestions from "
                       f"\"{engine.title}\".")
        # Select the top film so the user sees an explanation immediately.
        # selection_set() only QUEUES the <<TreeviewSelect>> event for the
        # next trip round the event loop, so we also call show_reasons()
        # ourselves rather than waiting for it.
        first = self.tree.get_children()[0]
        self.tree.selection_set(first)
        self.tree.focus(first)
        self.show_reasons()

    # ---- callbacks: explanations ------------------------------------------

    def selected_recommendation(self):
        """The Recommendation for the highlighted row, or None."""
        chosen = self.tree.selection()
        if not chosen:
            return None
        index = self.tree.index(chosen[0])
        if 0 <= index < len(self.results):
            return self.results[index]
        return None

    def show_reasons(self, event=None):
        """Show the built-in reasons for the highlighted film, instantly."""
        recommendation = self.selected_recommendation()
        if recommendation is None:
            return
        self._write_explanation(
            self.rule_explainer.explain(recommendation, self.preference))
        self.ai_button.config(state="disabled" if self._ai_busy else "normal")

    POLL_MILLISECONDS = 100
    TICK_MILLISECONDS = 300             # how often the waiting message updates

    def explain_with_ai(self):
        """Ask OpenRouter to write the explanation, on a background thread.

        Class 12 - MULTITHREADING. A network call takes seconds. If we made it
        here, on the thread that draws the window, the whole program would
        freeze until the reply arrived. So we hand the job to a second thread
        and let this one carry on drawing.

        The golden rule of Tkinter and threads: **only the main thread may
        touch anything belonging to Tkinter.** That includes `after()` itself,
        which is why the worker does not call it. Instead:

            worker thread  ->  puts the answer in a Queue  ->  main thread
            main thread    ->  checks that Queue every 100 ms

        A `queue.Queue` is built to be handed between threads safely, so it is
        the letterbox the two threads share. Nothing else crosses between them.
        """
        recommendation = self.selected_recommendation()
        if recommendation is None or self._ai_busy:
            return

        self._ai_busy = True
        self._ai_started = time.time()
        self._start_waiting_animation()

        worker = threading.Thread(target=self._ai_worker,
                                  args=(recommendation, self.preference),
                                  daemon=True)
        worker.start()
        # Scheduled from the MAIN thread, which is the only safe place to do it.
        self.after(self.POLL_MILLISECONDS, self._check_for_ai_reply)

    def _ai_worker(self, recommendation, preference):
        """Runs on the BACKGROUND thread. Touches nothing belonging to Tkinter."""
        # Only used if the explainer could not even be built - in which case
        # `problem` is set and the model name is never shown.
        model = "unknown"
        try:
            explainer = AIExplainer()
            model = explainer.model
            # explain_or_fallback never raises: if the key is missing or the
            # wifi is down it quietly returns the offline explanation.
            text = explainer.explain_or_fallback(recommendation, preference)
            problem = explainer.last_error
        except Exception as error:
            # Anything at all - a corrupt .env, a missing library. The answer
            # must reach the queue no matter what, or the button never comes
            # back and the tab is dead until the program is restarted.
            text = self.rule_explainer.explain(recommendation, preference)
            problem = f"{type(error).__name__}: {error}"

        self._ai_replies.put((text, problem, model))

    # ---- letting the user see that something is happening -----------------

    def _start_waiting_animation(self):
        """Make it obvious the program is working and has not frozen.

        Even a second of silence feels like a freeze, and a slow model can
        take thirty. With no feedback at all that is indistinguishable from
        a crash, so three things change the moment the button is pressed:
        the button says what it is doing, a barber-pole bar starts moving,
        and a counter ticks up.
        """
        self.ai_button.config(state="disabled", text="Asking the AI...")
        # before= keeps the bar to the left of the message, whatever order
        # the widgets were created in.
        self.progress.pack(side="left", padx=(12, 0), before=self.note)
        self.progress.start(12)
        self._write_explanation(
            "Asking the AI to write this up...\n\n"
            "This usually takes a second or two. Some models think to "
            "themselves before answering and take much longer - the counter "
            "below shows how long it has been. The window stays usable "
            "while you wait.")
        self._tick_waiting_message()

    def _tick_waiting_message(self):
        """Update the counter every 300 ms until the reply arrives."""
        if not self._ai_busy:
            return
        waited = time.time() - (self._ai_started or time.time())
        dots = "." * (1 + int(waited * 2) % 3)
        self._set_note(f"Waiting for the AI{dots}  ({waited:.0f}s)")
        self.after(self.TICK_MILLISECONDS, self._tick_waiting_message)

    def _stop_waiting_animation(self):
        """Put the controls back the way they were."""
        self.progress.stop()
        self.progress.pack_forget()
        self.ai_button.config(state="normal", text="Explain with AI")

    def _check_for_ai_reply(self):
        """Runs on the MAIN thread every 100 ms while a request is in flight."""
        try:
            text, problem, model = self._ai_replies.get_nowait()
        except queue.Empty:
            if self._ai_busy:
                self.after(self.POLL_MILLISECONDS, self._check_for_ai_reply)
            return
        self._show_ai_result(text, problem, model)

    def _show_ai_result(self, text, problem, model):
        """Runs on the MAIN thread once the reply is in."""
        self._ai_busy = False
        waited = time.time() - (self._ai_started or time.time())
        self._stop_waiting_animation()
        if problem:
            self._write_explanation(
                f"{text}\n\n[The AI could not be used, so these are the "
                f"built-in reasons.\nReason: {problem}]")
            self._set_note("AI unavailable - showing the built-in reasons.")
        else:
            self._write_explanation(text)
            self._set_note(f"Written by {model} in {waited:.0f}s.")

    # ---- exporting --------------------------------------------------------

    def current_rows(self):
        """The rows currently on screen, as dictionaries ready for export.

        The Browse tab has a method with this same name. That is what lets
        the File menu export whichever tab you happen to be looking at.
        """
        return [recommendation.to_dict() for recommendation in self.results]

    def export_results(self):
        """Save the recommendations using the ExportSession context manager."""
        rows = self.current_rows()
        if not rows:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="cinestat_recommendations.csv",
            filetypes=[("CSV file", "*.csv"), ("JSON file", "*.json")])
        if not path:
            return
        try:
            with ExportSession(path) as session:
                written = session.write(rows)
        except MovieDataError as error:
            messagebox.showerror("Export failed", str(error))
            return
        self._set_note(f"Saved {written} recommendations to {path}")

    # ---- drawing ----------------------------------------------------------

    def _refresh_table(self):
        """Empty the table and put the current recommendations back into it."""
        self.tree.delete(*self.tree.get_children())
        for recommendation in self.results:
            movie = recommendation.movie
            self.tree.insert("", "end", values=(
                recommendation.match,
                movie.name,
                movie.year,
                movie.genre,
                movie.rating,
                f"{movie.score:.1f}",
                f"{movie.runtime:.0f} min",
            ))
        self.export_button.config(state="normal" if self.results else "disabled")
        # Do not re-enable the AI button, or reset its label, while a
        # request is still in flight.
        if not self._ai_busy:
            self.ai_button.config(
                state="normal" if self.results else "disabled",
                text="Explain with AI")

    def _refresh_profile_label(self):
        """Show the profile the recommender will actually use."""
        preference = UserPreference.from_movies(self.liked)
        if preference.is_empty:
            self.profile_label.config(
                text="Your profile: nothing yet. Add a film above, or just "
                     "press Recommend to see the popular baseline.")
        else:
            self.profile_label.config(text=f"Your profile: {preference}")

    def _write_explanation(self, text):
        """Replace whatever is in the explanation box."""
        self.explanation.config(state="normal")
        self.explanation.delete("1.0", "end")
        self.explanation.insert("1.0", text)
        self.explanation.config(state="disabled")

    def _set_note(self, text):
        self.note.config(text=text)
