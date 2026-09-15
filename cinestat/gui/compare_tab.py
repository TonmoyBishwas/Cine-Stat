"""Compare tab - put two films side by side.

Syllabus Class 5: this tab is where the overloaded > operator earns its keep.
Instead of comparing two numbers by hand we simply write `film_a > film_b`,
because Movie defines __gt__.
"""

from tkinter import ttk

from .base_tab import BaseTab
from .widgets import MoviePicker
from ..utils import money


class CompareTab(BaseTab):
    """Shows the statistics of two films next to each other."""

    title = "Compare"

    # (label shown, function that turns a Movie into text)
    FIELDS = [
        ("Year", lambda m: str(m.year)),
        ("Genre", lambda m: m.genre),
        ("Age rating", lambda m: m.rating),
        ("Runtime", lambda m: f"{m.runtime:.0f} min"),
        ("Director", lambda m: m.director),
        ("Star", lambda m: m.star),
        ("Studio", lambda m: m.company),
        ("IMDb score", lambda m: f"{m.score:.1f} / 10"),
        ("Votes", lambda m: f"{m.votes:,}"),
        ("Budget", lambda m: money(m.budget)),
        ("Box office", lambda m: money(m.gross)),
        ("Profit", lambda m: money(m.profit)),
        ("Return on investment", lambda m: f"{m.roi:.2f}x"),
        ("Verdict", lambda m: m.verdict),
    ]

    def build_ui(self):
        self.add_heading(
            "Compare two films",
            "Search for two titles to see their numbers side by side.")

        pickers = ttk.Frame(self)
        pickers.pack(fill="x", pady=(0, self.px(14)))
        pickers.columnconfigure(0, weight=1)
        pickers.columnconfigure(1, weight=1)

        # The same custom widget used twice - that is why we wrote it as a class.
        self.left = MoviePicker(pickers, self.movies, "First film",
                                on_select=self.refresh)
        self.left.grid(row=0, column=0, sticky="ew", padx=(0, self.px(7)))

        self.right = MoviePicker(pickers, self.movies, "Second film",
                                 on_select=self.refresh)
        self.right.grid(row=0, column=1, sticky="ew", padx=(self.px(7), 0))

        self.verdict = ttk.Label(self, text="",
                                 font=self.theme.font(12, "bold"),
                                 wraplength=self.px(900), justify="center")
        self.verdict.pack(pady=(0, self.px(12)))

        self.table = ttk.Treeview(
            self, columns=("field", "left", "right"), show="headings", height=15)
        self.table.heading("field", text="")
        self.table.heading("left", text="First film")
        self.table.heading("right", text="Second film")
        self.table.column("field", width=self.px(200), anchor="w")
        self.table.column("left", width=self.px(270), anchor="center")
        self.table.column("right", width=self.px(270), anchor="center")
        self.table.pack(fill="both", expand=True)

        # Rows where one film clearly beats the other get a coloured tag.
        # The two tints come from the palette, so they are a pale green and a
        # pale blue in light mode and a deep green and a deep blue in dark -
        # a hard-coded "#E8F4EA" would be an invisible white smear on a dark
        # window, and unreadable under the white text sitting on it.
        self.table.tag_configure("left_wins", background=self.palette.first_wins)
        self.table.tag_configure("right_wins", background=self.palette.second_wins)

        self.refresh()

    def refresh(self):
        """Redraw the comparison. Called whenever either picker changes."""
        first, second = self.left.selected, self.right.selected
        if first is None or second is None:
            return

        self.table.heading("left", text=first.name)
        self.table.heading("right", text=second.name)
        self.table.delete(*self.table.get_children())

        for label, describe in self.FIELDS:
            tag = ""
            # Only highlight the rows where "bigger" clearly means "better".
            if label in ("Box office", "Profit", "Return on investment",
                         "IMDb score", "Votes"):
                attribute = {"Box office": "gross", "Profit": "profit",
                             "Return on investment": "roi",
                             "IMDb score": "score", "Votes": "votes"}[label]
                left_value = getattr(first, attribute)
                right_value = getattr(second, attribute)
                if left_value > right_value:
                    tag = "left_wins"
                elif right_value > left_value:
                    tag = "right_wins"

            self.table.insert("", "end",
                              values=(label, describe(first), describe(second)),
                              tags=(tag,))

        self._set_verdict(first, second)

    def _set_verdict(self, first, second):
        """Decide which film did better at the box office.

        `first > second` works because Movie defines __gt__ to compare gross.
        """
        if first == second:
            self.verdict.config(text="That is the same film twice.",
                                foreground=self.palette.muted)
            return

        if first > second:
            winner, loser = first, second
        elif second > first:
            winner, loser = second, first
        else:
            self.verdict.config(text="Both films took exactly the same amount.",
                                foreground=self.palette.muted)
            return

        times = winner.gross / loser.gross if loser.gross else 0
        self.verdict.config(
            text=f"{winner.name} took {money(winner.gross)} - "
                 f"{times:.1f}x more than {loser.name}.",
            foreground=self.palette.positive)
