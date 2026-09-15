"""Loading movie data from files.

Syllabus topics demonstrated here:
  Class 4 - abstract base class, inheritance, method overriding
  Class 5 - polymorphism (every loader is used the same way)
  Class 9 - File I/O and pathlib
"""

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd

from .movie import Movie
from .collection import MovieCollection
from .exceptions import DataFileError


class DataLoader(ABC):
    """ABSTRACT base class. You cannot create a DataLoader directly.

    It says: "every loader must have a load() method" but does not say how.
    Each subclass fills in that detail - that is METHOD OVERRIDING.
    The cleaning steps are written once here and inherited by all subclasses.
    """

    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    # Genres with fewer movies than this get grouped together as "Other".
    MIN_GENRE_COUNT = 100

    def __init__(self, path):
        self.path = Path(path)
        if not self.path.exists():
            raise DataFileError(f"Data file not found: {self.path}")

    @abstractmethod
    def load(self):
        """Read the file and return a raw pandas DataFrame.

        @abstractmethod means a subclass MUST write its own version of this.
        """

    def clean(self, df):
        """Tidy up the raw data. Shared by every subclass."""
        df = df.drop_duplicates()

        # Rows with no budget or no revenue are useless for our analysis.
        df = df.dropna(subset=["budget", "gross", "runtime", "rating", "genre"])
        df = df[(df["budget"] > 0) & (df["gross"] > 0)]

        # The 'released' column looks like "June 13, 1980 (United States)",
        # so the first word is normally the month. But a few rows hold a YEAR
        # there instead, so we keep only real month names and drop the rest.
        df = df.copy()
        df["month"] = df["released"].astype(str).str.split().str[0]
        df = df[df["month"].isin(self.MONTHS)]

        # Columns we calculate ourselves.
        df["profit"] = df["gross"] - df["budget"]
        df["roi"] = df["gross"] / df["budget"]

        # Rare genres become "Other" so charts and the model stay readable.
        counts = df["genre"].value_counts()
        common = counts[counts >= self.MIN_GENRE_COUNT].index
        df["genre_group"] = df["genre"].where(df["genre"].isin(common), "Other")

        return df.reset_index(drop=True)

    def load_clean(self):
        """Load the file and clean it in one step."""
        return self.clean(self.load())

    def to_collection(self):
        """Load, clean, and turn every row into a Movie object."""
        df = self.load_clean()
        collection = MovieCollection()
        for _, row in df.iterrows():
            collection.add(Movie.from_row(row))
        return collection


class CSVLoader(DataLoader):
    """Loads movies from a .csv file. Overrides load()."""

    def load(self):
        try:
            return pd.read_csv(self.path)
        except Exception as error:
            raise DataFileError(f"Could not read CSV {self.path}: {error}")


class JSONLoader(DataLoader):
    """Loads movies from a .json file. Overrides load() differently.

    Both loaders are used in exactly the same way:

        for loader in [CSVLoader("a.csv"), JSONLoader("b.json")]:
            movies = loader.to_collection()

    That is POLYMORPHISM - same call, different behaviour underneath.
    """

    def load(self):
        try:
            return pd.read_json(self.path)
        except Exception as error:
            raise DataFileError(f"Could not read JSON {self.path}: {error}")
