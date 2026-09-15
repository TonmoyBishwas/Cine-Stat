"""Browse tab - a searchable, sortable table of every film.

Syllabus Class 7: widgets, layout managers and callback functions.
"""

from tkinter import ttk

from .base_tab import BaseTab
from ..utils import money


class BrowseTab(BaseTab):
    """Lets the user search and filter the films, then sort the results."""

    title = "Browse"

    # (attribute on Movie, column heading, width in pixels)
    COLUMNS = [
        ("name", "Title", 250),
        ("year", "Year", 55),
        ("genre", "Genre", 95),
        ("rating", "Rating", 70),
        ("runtime", "Runtime", 70),
        ("score", "IMDb", 55),
        ("budget", "Budget", 90),
        ("gross", "Box office", 95),
        ("profit", "Profit", 95),
        ("roi", "ROI", 60),
        ("verdict", "Verdict", 85),
    ]

    #: Up for low-to-high, down for high-to-low - drawn in the heading of
    #: whichever column the table is sorted by.
    SORT_ARROWS = ("▲", "▼")

    def build_ui(self):
        # These have to exist before any callback can run.
        self.rows = []
        self._sort_by = None
        self._sort_reverse = False

        self.add_heading(
            "Browse the dataset",
            "Search for a title or narrow the list down with the filters, "
            "then click any column heading to sort by it.")
        self._build_filters()
        self._build_table()
        self.apply_filters()

    # ---- the filter bar ---------------------------------------------------

    def _build_filters(self):
        box = ttk.LabelFrame(self, text="Filters", padding=self.px(12))
        box.pack(fill="x", pady=(0, self.px(12)))

        first_year, last_year = self.movies.year_bounds()
        gap = self.px(18)

        ttk.Label(box, text="Title contains:").grid(row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(box, width=24)
        self.search_entry.grid(row=0, column=1, padx=(self.px(6), gap))
        # Pressing Enter in the box is the same as clicking Apply.
        self.search_entry.bind("<Return>", lambda event: self.apply_filters())

        ttk.Label(box, text="Genre:").grid(row=0, column=2, sticky="w")
        self.genre_box = ttk.Combobox(
            box, state="readonly", width=13,
            values=["All"] + self.movies.genres())
        self.genre_box.current(0)
        self.genre_box.grid(row=0, column=3, padx=(self.px(6), gap))

        ttk.Label(box, text="Rating:").grid(row=0, column=4, sticky="w")
        self.rating_box = ttk.Combobox(
            box, state="readonly", width=10,
            values=["All"] + self.movies.ratings())
        self.rating_box.current(0)
        self.rating_box.grid(row=0, column=5, padx=(self.px(6), gap))

        ttk.Label(box, text="Years:").grid(row=0, column=6, sticky="w")
        self.year_from = ttk.Spinbox(box, from_=first_year, to=last_year, width=6)
        self.year_from.set(first_year)
        self.year_from.grid(row=0, column=7, padx=(self.px(6), self.px(2)))

        ttk.Label(box, text="to").grid(row=0, column=8)
        self.year_to = ttk.Spinbox(box, from_=first_year, to=last_year, width=6)
        self.year_to.set(last_year)
        self.year_to.grid(row=0, column=9, padx=(self.px(2), gap))

        # command= is the CALLBACK: the function to run when the button is hit.
        # "Apply" is this tab's main action, so it gets the accent colour the
        # user chose in Windows Settings; "Reset" is an ordinary button.
        ttk.Button(box, text="Apply", style="Accent.TButton",
                   command=self.apply_filters).grid(
                       row=0, column=10, padx=self.px(3))
        ttk.Button(box, text="Reset", command=self.reset_filters).grid(
            row=0, column=11, padx=self.px(3))

    # ---- the table --------------------------------------------------------

    def _build_table(self):
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            frame, columns=[key for key, _, _ in self.COLUMNS],
            show="headings", selectmode="browse")

        for key, heading, width in self.COLUMNS:
            anchor = "w" if key in ("name", "genre", "rating", "verdict") else "e"
            # A lambda with a default argument captures THIS key, not the last.
            # anchor= on the heading as well as on the column: Windows lines a
            # heading up with its own figures, so a right-aligned money column
            # gets a right-aligned heading rather than a centred one.
            self.tree.heading(key, text=heading, anchor=anchor,
                              command=lambda k=key: self.sort_by(k))
            # px(): the widths are written for a 100% screen, so they have to
            # grow on a 150% one or the columns clip their own contents.
            self.tree.column(key, width=self.px(width), anchor=anchor,
                             stretch=(key == "name"))

        # Every other row slightly darker, the way Windows tables have looked
        # since Explorer grew a details view.
        self.theme.prepare_table(self.tree)

        scrollbar = ttk.Scrollbar(frame, orient="vertical",
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.status = ttk.Label(self, text="", style="Muted.TLabel")
        self.status.pack(anchor="w", pady=(self.px(8), 0))

    # ---- callbacks --------------------------------------------------------

    def apply_filters(self):
        """Work out which films match, then redraw the table."""
        text = self.search_entry.get().strip()
        # search() and in_year_range() are generators from MovieCollection.
        results = list(self.movies.search(text)) if text else list(self.movies)

        genre = self.genre_box.get()
        if genre != "All":
            results = [m for m in results if m.genre == genre]

        rating = self.rating_box.get()
        if rating != "All":
            results = [m for m in results if m.rating == rating]

        try:
            low, high = int(self.year_from.get()), int(self.year_to.get())
        except ValueError:
            low, high = self.movies.year_bounds()
        results = [m for m in results if low <= m.year <= high]

        self.rows = results
        self._sort_by = None
        self._refresh_table()

    def reset_filters(self):
        """Put every filter back to its starting value."""
        self.search_entry.delete(0, "end")
        self.genre_box.current(0)
        self.rating_box.current(0)
        first_year, last_year = self.movies.year_bounds()
        self.year_from.set(first_year)
        self.year_to.set(last_year)
        self.apply_filters()

    def sort_by(self, key):
        """Sort by the column that was clicked; click again to reverse it."""
        if not self.rows:
            return
        self._sort_reverse = (key == self._sort_by) and not self._sort_reverse
        self._sort_by = key
        self.rows.sort(key=lambda movie: getattr(movie, key),
                       reverse=self._sort_reverse)
        self._refresh_table()

    # ---- drawing ----------------------------------------------------------

    def _refresh_table(self):
        """Empty the table and put the current rows back into it."""
        self.tree.delete(*self.tree.get_children())
        for position, movie in enumerate(self.rows):
            self.tree.insert("", "end", tags=(self.theme.stripe_row(position),),
                             values=(
                movie.name,
                movie.year,
                movie.genre,
                movie.rating,
                f"{movie.runtime:.0f} min",
                f"{movie.score:.1f}",
                money(movie.budget),
                money(movie.gross),
                money(movie.profit),
                f"{movie.roi:.1f}x",
                movie.verdict,
            ))

        self._refresh_headings()
        arrow = ""
        if self._sort_by:
            arrow = f"  |  sorted by {self._sort_by}" \
                    f"{' (high to low)' if self._sort_reverse else ' (low to high)'}"
        self.status.config(
            text=f"Showing {len(self.rows):,} of {len(self.movies):,} films{arrow}")

    def _refresh_headings(self):
        """Put a small arrow on the heading the table is sorted by.

        Windows puts the sort arrow in the column heading itself rather than
        only in a line of text underneath, so someone glancing at the table
        can see at once which column it is ordered by and which way round.
        """
        pointer = self.SORT_ARROWS[1 if self._sort_reverse else 0]
        for key, heading, _ in self.COLUMNS:
            text = f"{heading} {pointer}" if key == self._sort_by else heading
            self.tree.heading(key, text=text)      # anchor is left as set

    # ---- used by the File menu --------------------------------------------

    def current_rows(self):
        """The rows currently on screen, as dictionaries ready for export."""
        return [movie.to_dict() for movie in self.rows]
