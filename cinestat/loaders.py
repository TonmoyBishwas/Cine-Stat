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

    # ---- choosing a loader automatically ----------------------------------

    @classmethod
    def for_file(cls, path, **kwargs):
        """Pick the right loader for this file by peeking at its first line.

        A @classmethod on the ABSTRACT parent that hands back one of its own
        CHILDREN. That is called a FACTORY METHOD: the caller says "load this
        file" and never has to know which of the three classes did the work.

            movies = DataLoader.for_file("data/movies.csv").to_collection()
            movies = DataLoader.for_file("data/tmdb.csv").to_collection()

        Both lines work, and the rest of the program cannot tell them apart.
        """
        path = Path(path)
        if path.suffix.lower() == ".json":
            return JSONLoader(path, **kwargs)
        if not path.exists():
            raise DataFileError(f"Data file not found: {path}")

        try:
            # `with` again: without it this handle stays open until Python
            # happens to garbage-collect it.
            with path.open(encoding="utf-8", errors="replace") as handle:
                header = handle.readline()
        except OSError as error:
            raise DataFileError(f"Could not read {path}: {error}")
        columns = {name.strip().strip('"') for name in header.split(",")}

        # movies.csv calls them name/gross; the TMDB export title/revenue.
        if "revenue" in columns and "name" not in columns:
            return TMDBLoader(path, **kwargs)
        return CSVLoader(path, **kwargs)


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


class TMDBLoader(DataLoader):
    """Loads the very large TMDB dataset from Kaggle (about 1-3 million rows).

    Source: https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies

    Two problems have to be solved, and each one is solved by OVERRIDING a
    method the parent already wrote:

    1. **The file is far too big to open in one go.** A few million rows would
       fill the computer's memory. `load()` therefore reads the file in
       CHUNKS - a few hundred thousand rows at a time - throws away the rows
       it cannot use, and only keeps the survivors. Memory use stays flat no
       matter how big the file is.

    2. **The column names are different.** TMDB calls the box office `revenue`
       and the title `title`. COLUMN_MAP below translates them into the names
       the rest of CineStat already understands, so `Movie`, `MovieCollection`,
       every analyzer, the predictor and all five tabs keep working untouched.
       If your copy of the file uses slightly different names, this dictionary
       is the only thing you need to edit.

    Honest warning, worth saying in the demo: the file has millions of titles,
    but only a small fraction of them record a budget AND a box office. The
    rest are shorts, unreleased films and entries nobody filled in. We keep
    the ones with real money figures, which is still several times more films
    than movies.csv has.

    Syllabus Class 4 and 5: a third subclass of DataLoader, used in exactly
    the same way as the other two. That is inheritance and polymorphism.
    """

    # Their column name  ->  our column name
    COLUMN_MAP = {
        "title": "name",
        "release_date": "release_date",
        "revenue": "gross",
        "budget": "budget",
        "runtime": "runtime",
        "vote_average": "score",
        "vote_count": "votes",
        "genres": "genre",
        "production_companies": "company",
        "original_language": "language",
        "adult": "adult",
        "status": "status",
    }

    CHUNK_SIZE = 200_000        # rows read into memory at a time
    MIN_VOTES = 10              # ignore films almost nobody has rated

    def __init__(self, path, max_movies=None):
        super().__init__(path)
        # A safety cap so the desktop app stays quick. None means "no cap".
        self.max_movies = max_movies

    # ---- overriding load() ------------------------------------------------

    def load(self):
        """Override: stream the huge CSV in chunks and keep the usable rows."""
        kept = []
        rows_seen = 0
        try:
            # `with` matters here. Reading in chunks keeps the file OPEN
            # between chunks, and we may stop early (max_movies) or bail out
            # with an error. The context manager closes the file either way -
            # the same reason ExportSession exists. Class 9.
            with pd.read_csv(self.path, chunksize=self.CHUNK_SIZE,
                             low_memory=False) as reader:
                for chunk in reader:
                    rows_seen += len(chunk)
                    usable = self._keep_usable(chunk)
                    if not usable.empty:
                        kept.append(usable)
                    if self.max_movies and \
                            sum(len(part) for part in kept) >= self.max_movies:
                        break
        except DataFileError:
            raise
        except Exception as error:
            raise DataFileError(f"Could not read {self.path}: {error}")

        if not kept:
            raise DataFileError(
                f"Read {rows_seen:,} rows from {self.path.name} but none of "
                f"them had both a budget and a box-office figure. Check that "
                f"TMDBLoader.COLUMN_MAP matches the column names in your file.")

        df = pd.concat(kept, ignore_index=True)
        if self.max_movies:
            df = df.head(self.max_movies)
        return df

    # ---- the per-chunk work -----------------------------------------------

    def _keep_usable(self, chunk):
        """Rename the columns, drop the unusable rows, return what is left."""
        available = {old: new for old, new in self.COLUMN_MAP.items()
                     if old in chunk.columns}
        if "title" not in available:
            raise DataFileError(
                f"{self.path.name} has no 'title' column. Its columns are: "
                f"{', '.join(list(chunk.columns)[:12])}...")

        df = chunk[list(available)].rename(columns=available).copy()

        # Columns the file simply does not have. Creating them empty here
        # means the rest of the method never has to ask whether they exist.
        for column in ("genre", "company", "release_date"):
            if column not in df.columns:
                df[column] = ""

        # Only released films with real money figures are any use to us.
        if "status" in df.columns:
            df = df[df["status"].astype(str).str.strip() == "Released"]
        for column in ("budget", "gross", "runtime", "score", "votes"):
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")
            else:
                df[column] = 0.0
        df = df.dropna(subset=["budget", "gross"])
        df = df[(df["budget"] > 0) & (df["gross"] > 0)]
        df = df[df["votes"].fillna(0) >= self.MIN_VOTES]
        if df.empty:
            return df

        return self._build_our_columns(df)

    def _build_our_columns(self, df):
        """Create the exact columns the rest of CineStat expects."""
        # TMDB stores the date as 2009-12-15. The parent's clean() wants text
        # that starts with a month name, like "December 15, 2009".
        dates = pd.to_datetime(df["release_date"], errors="coerce")
        df = df[dates.notna()].copy()
        dates = dates[dates.notna()]
        df["year"] = dates.dt.year
        df["released"] = dates.dt.strftime("%B %d, %Y") + " (United States)"

        # "Drama, Crime, Thriller" -> "Drama". One main genre, like movies.csv.
        df["genre"] = (df["genre"]
                       .fillna("Unknown").astype(str)
                       .str.split(",").str[0].str.strip()
                       .replace("", "Unknown"))

        df["company"] = (df["company"]
                         .fillna("").astype(str)
                         .str.split(",").str[0].str.strip())

        # This export has no age certification (G / PG / PG-13 / R). All we
        # are told is whether a film is adult-only, so that is all we claim.
        if "adult" in df.columns:
            adult = df["adult"].astype(str).str.lower().isin(["true", "1"])
            df["rating"] = adult.map({True: "NC-17", False: "Not Rated"})
        else:
            df["rating"] = "Not Rated"

        # Columns movies.csv has that this file does not.
        df["director"] = ""
        df["writer"] = ""
        df["star"] = ""
        df["country"] = df.get("language", "")

        df = df.drop(columns=[c for c in ("status", "language", "adult",
                                          "release_date") if c in df.columns])
        return df
