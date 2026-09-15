"""A small custom widget we wrote ourselves and then reuse.

Syllabus Class 7 and 8: building our own widget by inheriting from an existing
one, so the Compare tab can use the same picker twice without copying code.
"""

from tkinter import ttk


class MoviePicker(ttk.LabelFrame):
    """A search box plus a dropdown for choosing one film.

    The full list has thousands of titles, which is far too many for a plain
    dropdown, so typing in the search box narrows the list down.
    """

    MAX_RESULTS = 200

    def __init__(self, parent, collection, label="Choose a film",
                 on_select=None):
        # The picker is built inside a tab, and the tab knows the theme, so
        # the padding here can be scaled for the screen like everything else.
        scale = getattr(getattr(parent.winfo_toplevel(), "theme", None),
                        "px", lambda pixels: pixels)
        super().__init__(parent, text=label, padding=scale(12))
        self.collection = collection
        self.on_select = on_select      # a function to call after a choice
        self.selected = None

        ttk.Label(self, text="Search by title:").pack(anchor="w")

        self.search_entry = ttk.Entry(self)
        self.search_entry.pack(fill="x", pady=(scale(3), scale(9)))
        # bind() connects an event (a key being released) to a function.
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.combo = ttk.Combobox(self, state="readonly")
        self.combo.pack(fill="x")
        self.combo.bind("<<ComboboxSelected>>", self._on_choice)

        # notify=False: while we are still inside __init__ the tab that owns
        # this picker is only half built, so it is not ready to be told about
        # a selection yet. The tab refreshes itself once at the end instead.
        self._fill(self.collection.names(), notify=False)

    # ---- internal helpers -------------------------------------------------

    def _fill(self, names, notify=True):
        """Put a list of titles into the dropdown and select the first one."""
        shown = names[: self.MAX_RESULTS]
        self.combo["values"] = shown
        if shown:
            self.combo.current(0)
            self._choose(notify=notify)

    def _choose(self, notify=True):
        """Remember the chosen film, and optionally tell the parent tab."""
        name = self.combo.get()
        if not name:
            return
        self.selected = self.collection.find(name)
        if notify and self.on_select:
            self.on_select()

    def _on_search(self, event=None):
        """Runs every time a key is released in the search box."""
        text = self.search_entry.get().strip()
        if not text:
            self._fill(self.collection.names())
            return
        # search() is a generator, so sorted() pulls the matches out of it.
        matches = sorted(movie.name for movie in self.collection.search(text))
        self._fill(matches)

    def _on_choice(self, event=None):
        """Runs when the user picks a title from the dropdown."""
        self._choose(notify=True)
