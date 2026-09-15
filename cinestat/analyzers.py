"""The analysis classes.

Syllabus topics demonstrated here:
  Class 4  - abstract base class, inheritance
  Class 5  - polymorphism, multiple inheritance (FinancialAnalyzer)
  Class 11 - decorators (@timed on run())
"""

from abc import ABC, abstractmethod

from .utils import timed, money, ExportSession


class ExportMixin:
    """A small extra class that adds saving to a file.

    A "mixin" is not meant to be used on its own. It is mixed into another
    class through MULTIPLE INHERITANCE to add one specific ability.
    """

    def export(self, path):
        """Save this analyzer's result table to CSV or JSON."""
        rows = self.results.reset_index().to_dict(orient="records")
        with ExportSession(path) as session:
            session.write(rows)
        return path


class BaseAnalyzer(ABC):
    """ABSTRACT base class for every kind of analysis.

    It handles the parts every analyzer shares (holding the data, running,
    printing) and leaves the actual calculation to each subclass.
    """

    title = "Analysis"

    def __init__(self, collection):
        self.collection = collection
        self.df = collection.to_dataframe()
        self.results = None          # filled in by analyze()

    @abstractmethod
    def analyze(self):
        """Do the calculation and return a DataFrame.

        Every subclass MUST write its own version of this method.
        """

    @abstractmethod
    def summary(self):
        """Return a list of short plain-English findings."""

    @timed                           # <- Class 11: the decorator in use
    def run(self):
        """Run the analysis and remember the result."""
        self.results = self.analyze()
        return self.results

    def report(self):
        """Print the title and the findings."""
        if self.results is None:
            self.run()
        print(f"\n=== {self.title} ===")
        for line in self.summary():
            print(" *", line)
        return self.results

    def __str__(self):
        return f"{self.__class__.__name__}({len(self.collection)} movies)"


class GenreAnalyzer(BaseAnalyzer):
    """Which genre earns the most, and which is the safest bet?"""

    title = "Genre Analysis"

    def analyze(self):
        grouped = self.df.groupby("genre_group").agg(
            movies=("name", "count"),
            avg_budget=("budget", "mean"),
            avg_gross=("gross", "mean"),
            avg_profit=("profit", "mean"),
            median_roi=("roi", "median"),
            avg_score=("score", "mean"),
        )
        # Share of movies in this genre that failed to earn back their budget.
        grouped["flop_rate"] = (
            self.df.assign(flop=self.df["gross"] < self.df["budget"])
            .groupby("genre_group")["flop"].mean() * 100
        )
        return grouped.sort_values("median_roi", ascending=False).round(2)

    def summary(self):
        r = self.results
        best_roi = r["median_roi"].idxmax()
        best_gross = r["avg_gross"].idxmax()
        safest = r["flop_rate"].idxmin()
        return [
            f"Best return on investment: {best_roi} "
            f"({r.loc[best_roi, 'median_roi']:.2f}x the budget, typically)",
            f"Biggest average earner: {best_gross} "
            f"({money(r.loc[best_gross, 'avg_gross'])} per film)",
            f"Safest genre: {safest} "
            f"(only {r.loc[safest, 'flop_rate']:.1f}% of films lose money)",
        ]


class TrendAnalyzer(BaseAnalyzer):
    """How has the industry changed between 1980 and 2020?"""

    title = "Trends Over Time"

    def analyze(self):
        return self.df.groupby("year").agg(
            movies=("name", "count"),
            avg_budget=("budget", "mean"),
            avg_gross=("gross", "mean"),
            avg_score=("score", "mean"),
            median_roi=("roi", "median"),
        ).round(2)

    def summary(self):
        r = self.results
        first, last = r.index.min(), r.index.max()
        budget_growth = r.loc[last, "avg_budget"] / r.loc[first, "avg_budget"]
        return [
            f"Average budget in {first}: {money(r.loc[first, 'avg_budget'])}; "
            f"in {last}: {money(r.loc[last, 'avg_budget'])}",
            f"That is {budget_growth:.1f}x more expensive to make a film",
            f"Average IMDb score moved from {r.loc[first, 'avg_score']:.2f} "
            f"to {r.loc[last, 'avg_score']:.2f}",
        ]


class FinancialAnalyzer(BaseAnalyzer, ExportMixin):
    """Profit, risk and the effect of the age rating.

    Note the class line above: it inherits from TWO parents at once.
    That is MULTIPLE INHERITANCE - it is a BaseAnalyzer *and* it can export.
    """

    title = "Financial Analysis"

    def analyze(self):
        return self.df.groupby("rating").agg(
            movies=("name", "count"),
            avg_budget=("budget", "mean"),
            avg_gross=("gross", "mean"),
            avg_profit=("profit", "mean"),
            median_roi=("roi", "median"),
        ).sort_values("avg_gross", ascending=False).round(2)

    def summary(self):
        r = self.results
        flop_rate = (self.df["gross"] < self.df["budget"]).mean() * 100
        richest = self.df.loc[self.df["profit"].idxmax()]
        return [
            f"{flop_rate:.1f}% of all films failed to earn back their budget",
            f"Most profitable film: {richest['name']} ({richest['year']}) "
            f"made {money(richest['profit'])}",
            f"Highest grossing age rating: {r['avg_gross'].idxmax()} "
            f"({money(r['avg_gross'].max())} average)",
        ]
