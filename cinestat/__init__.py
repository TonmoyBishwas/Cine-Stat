"""CineStat - a movie analysis package for the DS 1116 OOP lab project.

Importing the package gives you the main classes directly:

    from cinestat import CSVLoader, MovieCollection, SuccessPredictor
"""

from .exceptions import (
    MovieDataError,
    InvalidBudgetError,
    MovieNotFoundError,
    ModelNotTrainedError,
    DataFileError,
)
from .movie import Movie
from .collection import MovieCollection
from .loaders import DataLoader, CSVLoader, JSONLoader
from .analyzers import BaseAnalyzer, GenreAnalyzer, TrendAnalyzer, FinancialAnalyzer
from .predictor import SuccessPredictor

__version__ = "1.0"

# Controls what "from cinestat import *" brings in.
__all__ = [
    "Movie", "MovieCollection",
    "DataLoader", "CSVLoader", "JSONLoader",
    "BaseAnalyzer", "GenreAnalyzer", "TrendAnalyzer", "FinancialAnalyzer",
    "SuccessPredictor",
    "MovieDataError", "InvalidBudgetError", "MovieNotFoundError",
    "ModelNotTrainedError", "DataFileError",
]
