"""Predict tab - the linear regression, driven by a form.

Syllabus Class 9: this is where custom exceptions become visible to the user.
If the budget typed in is not a valid number, SuccessPredictor raises
InvalidBudgetError, this tab catches it, and shows a friendly message box
instead of letting the program crash.
"""

from tkinter import ttk, messagebox

from .base_tab import BaseTab
from ..utils import money
from ..exceptions import MovieDataError


class PredictTab(BaseTab):
    """Asks for the details of an imaginary film and predicts what it earns."""

    title = "Predict"

    #: A verdict maps to a *name* in the palette rather than to a colour, so
    #: the same three words come out readable in light mode and in dark mode.
    #: Hard-coding "#2E6E3E" here would leave a dark green word sitting on a
    #: #202020 window, which is very nearly invisible.
    VERDICT_COLOURS = {
        "Hit": "positive",
        "Break-even": "warning",
        "Flop": "negative",
    }

    def verdict_colour(self, verdict):
        """The colour this verdict should be written in, from the palette."""
        return getattr(self.palette, self.VERDICT_COLOURS[verdict])

    def build_ui(self):
        self.add_heading(
            "Will my film make money?",
            "Fill in the details of a film you are thinking of making. The "
            "model was trained only on facts known BEFORE a film is released, "
            "so it never uses reviews or vote counts.")

        columns = ttk.Frame(self)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=0)
        columns.columnconfigure(1, weight=1)
        columns.rowconfigure(0, weight=1)

        self._build_form(columns)
        self._build_results(columns)
        self.predict()

    # ---- the input form ---------------------------------------------------

    def _build_form(self, parent):
        form = ttk.LabelFrame(parent, text="Your film", padding=self.px(16))
        form.grid(row=0, column=0, sticky="nsew", padx=(0, self.px(16)))

        choices = self.predictor.options()
        first_year, last_year = self.movies.year_bounds()

        ttk.Label(form, text="Budget (US dollars)").grid(
            row=0, column=0, sticky="w", pady=(0, self.px(2)))
        self.budget_entry = ttk.Entry(form, width=22)
        self.budget_entry.insert(0, "50000000")
        self.budget_entry.grid(row=1, column=0, sticky="ew", pady=(0, self.px(10)))
        # Pressing Enter runs the prediction, same as the button.
        self.budget_entry.bind("<Return>", lambda event: self.predict())

        ttk.Label(form, text="Genre").grid(row=2, column=0, sticky="w", pady=(0, self.px(2)))
        self.genre_box = ttk.Combobox(form, state="readonly", width=20,
                                      values=choices["genres"])
        self.genre_box.set("Action" if "Action" in choices["genres"]
                           else choices["genres"][0])
        self.genre_box.grid(row=3, column=0, sticky="ew", pady=(0, self.px(10)))

        ttk.Label(form, text="Age rating").grid(row=4, column=0, sticky="w", pady=(0, self.px(2)))
        self.rating_box = ttk.Combobox(form, state="readonly", width=20,
                                       values=choices["ratings"])
        self.rating_box.set("PG-13" if "PG-13" in choices["ratings"]
                            else choices["ratings"][0])
        self.rating_box.grid(row=5, column=0, sticky="ew", pady=(0, self.px(10)))

        ttk.Label(form, text="Runtime (minutes)").grid(
            row=6, column=0, sticky="w", pady=(0, self.px(2)))
        self.runtime_spin = ttk.Spinbox(form, from_=40, to=300, width=20)
        self.runtime_spin.set(120)
        self.runtime_spin.grid(row=7, column=0, sticky="ew", pady=(0, self.px(10)))

        ttk.Label(form, text="Release year").grid(
            row=8, column=0, sticky="w", pady=(0, self.px(2)))
        self.year_spin = ttk.Spinbox(form, from_=first_year, to=last_year + 10,
                                     width=20)
        self.year_spin.set(last_year)
        self.year_spin.grid(row=9, column=0, sticky="ew", pady=(0, self.px(10)))

        ttk.Label(form, text="Release month").grid(
            row=10, column=0, sticky="w", pady=(0, self.px(2)))
        self.month_box = ttk.Combobox(form, state="readonly", width=20,
                                      values=choices["months"])
        self.month_box.set("July")
        self.month_box.grid(row=11, column=0, sticky="ew", pady=(0, self.px(14)))

        # The one thing this tab exists to do, so it wears the accent colour.
        ttk.Button(form, text="Predict", style="Accent.TButton",
                   command=self.predict).grid(row=12, column=0, sticky="ew")

    # ---- the results panel ------------------------------------------------

    def _build_results(self, parent):
        panel = ttk.LabelFrame(parent, text="Prediction", padding=self.px(16))
        panel.grid(row=0, column=1, sticky="nsew")

        # Windows writes a big headline number in a LIGHTER weight, not a
        # heavier one - compare the figures on the Settings pages. That is
        # what "Big.TLabel" asks the theme for.
        self.gross_label = ttk.Label(panel, text="", style="Big.TLabel")
        self.gross_label.pack(anchor="w")
        ttk.Label(panel, text="predicted box office",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, self.px(18)))

        self.detail_labels = {}
        for field in ("Budget", "Profit", "Return on investment"):
            row = ttk.Frame(panel)
            row.pack(fill="x", pady=self.px(3))
            ttk.Label(row, text=field, width=22,
                      style="Muted.TLabel").pack(side="left")
            value = ttk.Label(row, text="", style="Value.TLabel")
            value.pack(side="left")
            self.detail_labels[field] = value

        self.verdict_label = ttk.Label(panel, text="", style="Verdict.TLabel")
        self.verdict_label.pack(anchor="w", pady=(self.px(20), self.px(4)))

        self.explain_label = ttk.Label(panel, text="",
                                       wraplength=self.px(440),
                                       justify="left", style="Muted.TLabel")
        self.explain_label.pack(anchor="w")

        ttk.Separator(panel, orient="horizontal").pack(
            fill="x", pady=self.px(16))

        self.accuracy_label = ttk.Label(panel, text="",
                                        wraplength=self.px(440),
                                        justify="left", style="Muted.TLabel")
        self.accuracy_label.pack(anchor="w")

    # ---- the callback -----------------------------------------------------

    def predict(self):
        """Read the form, run the model, and show the answer.

        Everything is inside try/except, so a bad value shows a message box
        rather than crashing the program.
        """
        try:
            result = self.predictor.predict(
                budget=self.budget_entry.get(),
                genre=self.genre_box.get(),
                rating=self.rating_box.get(),
                runtime=self.runtime_spin.get(),
                year=self.year_spin.get(),
                month=self.month_box.get(),
            )
        except MovieDataError as error:
            # Catches InvalidBudgetError and ModelNotTrainedError together,
            # because both inherit from MovieDataError.
            messagebox.showerror("Cannot make a prediction", str(error))
            return
        except ValueError as error:
            messagebox.showerror("Cannot make a prediction",
                                 f"Please check the runtime and year.\n\n{error}")
            return

        budget = float(self.budget_entry.get())
        self.gross_label.config(text=money(result["gross"]))
        self.detail_labels["Budget"].config(text=money(budget))
        self.detail_labels["Profit"].config(
            text=money(result["profit"]),
            foreground=(self.palette.positive if result["profit"] >= 0
                        else self.palette.negative))
        self.detail_labels["Return on investment"].config(
            text=f"{result['roi']:.2f}x")

        verdict = result["verdict"]
        self.verdict_label.config(text=verdict,
                                  foreground=self.verdict_colour(verdict))

        if verdict == "Hit":
            message = ("The model expects this film to earn back at least twice "
                       "its budget, which is the usual bar for a real success.")
        elif verdict == "Break-even":
            message = ("The model expects this film to make its money back, but "
                       "not much more. Once marketing is paid for it could still "
                       "end up losing money.")
        else:
            message = ("The model expects this film to earn less than it cost "
                       "to make. About a third of real films end up here.")
        self.explain_label.config(text=message)

        self.accuracy_label.config(
            text=(f"How much to trust this: the model explains about "
                  f"{result['r2'] * 100:.0f}% of the difference between real "
                  f"films (R-squared {result['r2']:.3f}), and is off by "
                  f"{money(result['mae'])} on average. Budget does almost all "
                  f"of the work - a script, a cast and a marketing campaign are "
                  f"not things a spreadsheet can measure. Treat this as a rough "
                  f"guide, not a promise."))
