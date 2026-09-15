"""Charts tab - draws the notebook's charts inside the window.

Syllabus Class 7: putting a matplotlib figure inside a Tkinter frame.
"""

from tkinter import ttk

import numpy as np
import matplotlib
matplotlib.use("TkAgg")          # tell matplotlib to draw into Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)

from .base_tab import BaseTab
from ..analyzers import GenreAnalyzer, TrendAnalyzer, FinancialAnalyzer
from ..loaders import DataLoader


class ChartsTab(BaseTab):
    """Shows one chart at a time, chosen from a dropdown."""

    title = "Charts"

    def build_ui(self):
        # Every chart is a method on this class. The dictionary maps the name
        # the user sees to the method that draws it. Storing functions in a
        # dictionary like this is Syllabus Class 11: functions as objects.
        self.charts = {
            "Average box office by genre": self.chart_gross_by_genre,
            "Return on investment by genre": self.chart_roi_by_genre,
            "Risk: flop rate by genre": self.chart_flop_by_genre,
            "Budget and box office over time": self.chart_over_time,
            "Budget vs box office": self.chart_budget_vs_gross,
            "Budget vs IMDb score": self.chart_budget_vs_score,
            "Best month to release a film": self.chart_by_month,
            "Box office by age rating": self.chart_by_rating,
        }

        self.add_heading(
            "Charts",
            "Pick a chart from the dropdown. Use the toolbar underneath to "
            "zoom, drag, or save a chart as an image.")

        self.df = self.movies.to_dataframe()

        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, self.px(12)))
        ttk.Label(bar, text="Chart:").pack(side="left")
        self.chooser = ttk.Combobox(bar, state="readonly", width=40,
                                    values=list(self.charts.keys()))
        self.chooser.current(0)
        self.chooser.pack(side="left", padx=self.px(8))
        self.chooser.bind("<<ComboboxSelected>>", self.draw)

        # dpi=100 was written for a 100% screen. On a 150% one the figure
        # would be drawn at two thirds size and then stretched by Tk, which
        # is exactly the blurring that claiming DPI awareness was meant to
        # avoid - so the figure is told about the screen as well.
        self.figure = Figure(figsize=(9, 5), dpi=100 * self.theme.scale)
        self.figure.patch.set_facecolor(self.palette.surface)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        widget = self.canvas.get_tk_widget()
        # The canvas is a plain tk widget, so no ttk style reaches it. Left
        # alone it is a white rectangle, which shows as a bright halo around
        # the chart on a dark window.
        widget.configure(background=self.palette.surface,
                         highlightthickness=0, borderwidth=0)
        widget.pack(fill="both", expand=True)

        toolbar_frame = ttk.Frame(self)
        toolbar_frame.pack(fill="x")
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        # The zoom-and-save toolbar is built out of old-style tk buttons, so
        # it arrives white whatever the rest of the window is doing.
        self.theme.style_toolbar(self.toolbar)

        self.draw()

    # ---- the one callback -------------------------------------------------

    def draw(self, event=None):
        """Clear the figure, run the chosen chart method, and show it.

        The theme is applied AFTER the chart method rather than before it,
        because that is when the things being recoloured exist: a chart only
        has a legend once the method that calls ax.legend() has run.
        """
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        self.charts[self.chooser.get()](axes)
        self.theme.style_axes(axes)
        self.theme.style_legend(axes)
        self.figure.tight_layout()
        self.canvas.draw()

    # ---- the chart methods ------------------------------------------------

    def chart_gross_by_genre(self, ax):
        table = GenreAnalyzer(self.movies).run().sort_values("avg_gross")
        ax.barh(table.index, table["avg_gross"] / 1e6,
                color=self.theme.chart("green"))
        ax.set_title("Average box office by genre")
        ax.set_xlabel("$ millions per film")

    def chart_roi_by_genre(self, ax):
        table = GenreAnalyzer(self.movies).run().sort_values("median_roi")
        ax.barh(table.index, table["median_roi"],
                color=self.theme.chart("blue"))
        ax.axvline(1.0, color=self.theme.chart("rule"), linestyle="--",
                   label="break even")
        ax.set_title("Typical return per dollar spent")
        ax.set_xlabel("ROI (times the budget)")
        ax.legend()

    def chart_flop_by_genre(self, ax):
        table = GenreAnalyzer(self.movies).run().sort_values("flop_rate")
        ax.barh(table.index, table["flop_rate"],
                color=self.theme.chart("red"))
        ax.set_title("Share of films that failed to earn back their budget")
        ax.set_xlabel("Flop rate (%)")

    def chart_over_time(self, ax):
        table = TrendAnalyzer(self.movies).run()
        ax.plot(table.index, table["avg_budget"] / 1e6, marker="o",
                markersize=3, color=self.theme.chart("red"), label="Budget")
        ax.plot(table.index, table["avg_gross"] / 1e6, marker="s",
                markersize=3, color=self.theme.chart("green"),
                label="Box office")
        ax.set_title("Films cost more - and earn more - than they used to")
        ax.set_xlabel("Year")
        ax.set_ylabel("$ millions")
        ax.legend()

    def chart_budget_vs_gross(self, ax):
        ax.scatter(self.df["budget"] / 1e6, self.df["gross"] / 1e6,
                   alpha=0.25, s=10, color=self.theme.chart("blue"))
        slope, intercept = np.polyfit(self.df["budget"], self.df["gross"], 1)
        line_x = np.linspace(self.df["budget"].min(), self.df["budget"].max(), 100)
        ax.plot(line_x / 1e6, (slope * line_x + intercept) / 1e6,
                color=self.theme.chart("rule"), linewidth=2,
                label=f"${slope:.2f} back per $1 spent")
        ax.set_title(f"Budget vs box office "
                     f"(correlation {self.df['budget'].corr(self.df['gross']):.2f})")
        ax.set_xlabel("Budget ($ millions)")
        ax.set_ylabel("Box office ($ millions)")
        ax.legend()

    def chart_budget_vs_score(self, ax):
        ax.scatter(self.df["budget"] / 1e6, self.df["score"],
                   alpha=0.25, s=10, color=self.theme.chart("purple"))
        slope, intercept = np.polyfit(self.df["budget"], self.df["score"], 1)
        line_x = np.linspace(self.df["budget"].min(), self.df["budget"].max(), 100)
        ax.plot(line_x / 1e6, slope * line_x + intercept,
                color=self.theme.chart("rule"), linewidth=2,
                label="best fit (almost flat)")
        correlation = self.df["budget"].corr(self.df["score"])
        ax.set_title(f"Money does not buy a good film "
                     f"(correlation only {correlation:.2f})")
        ax.set_xlabel("Budget ($ millions)")
        ax.set_ylabel("IMDb score out of 10")
        ax.legend()

    def chart_by_month(self, ax):
        table = (self.df.groupby("month")["gross"].mean()
                 .reindex(DataLoader.MONTHS))
        average = table.mean()
        above, below = self.theme.chart("red"), self.theme.chart("blue")
        colors = [above if value > average else below for value in table]
        ax.bar(range(len(table)), table.values / 1e6, color=colors)
        ax.set_xticks(range(len(table)))
        ax.set_xticklabels([m[:3] for m in table.index])
        # "black" would be an invisible line on a dark window, so the
        # reference line takes its colour from the theme like everything else.
        ax.axhline(average / 1e6, color=self.theme.chart("guide"),
                   linestyle="--", label="yearly average")
        ax.set_title("Films released in summer and at Christmas earn more")
        ax.set_ylabel("Average box office ($ millions)")
        ax.legend()

    def chart_by_rating(self, ax):
        table = FinancialAnalyzer(self.movies).run()
        main = [r for r in ["G", "PG", "PG-13", "R", "NC-17"] if r in table.index]
        subset = table.loc[main]
        positions = np.arange(len(subset))
        ax.bar(positions - 0.2, subset["avg_budget"] / 1e6, 0.4,
               label="Budget", color=self.theme.chart("red"))
        ax.bar(positions + 0.2, subset["avg_gross"] / 1e6, 0.4,
               label="Box office", color=self.theme.chart("green"))
        ax.set_xticks(positions)
        ax.set_xticklabels(subset.index)
        ax.set_title("Average budget vs box office by age rating")
        ax.set_ylabel("$ millions")
        ax.legend()
