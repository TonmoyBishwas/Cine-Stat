"""CineStat - a movie analysis package for the DS 1116 OOP lab project.

Importing the package gives you the main classes directly:

    from cinestat import CSVLoader, MovieCollection, SuccessPredictor
    from cinestat import UserPreference, ContentRecommender, AIExplainer
"""

from .exceptions import (
    MovieDataError,
    InvalidBudgetError,
    InvalidGrossError,
    MovieNotFoundError,
    ModelNotTrainedError,
    DataFileError,
    InvalidPreferenceError,
    AIServiceError,
)
from .movie import Movie
from .collection import MovieCollection
from .loaders import DataLoader, CSVLoader, JSONLoader, TMDBLoader
from .analyzers import BaseAnalyzer, GenreAnalyzer, TrendAnalyzer, FinancialAnalyzer
from .predictor import SuccessPredictor
from .preferences import UserPreference
from .recommenders import (
    Recommendation,
    BaseRecommender,
    ContentRecommender,
    SimilarityRecommender,
    PopularityRecommender,
)
from .explainers import (
    BaseExplainer,
    RuleExplainer,
    AIExplainer,
    build_explainer,
)

__version__ = "1.1"

# Controls what "from cinestat import *" brings in.
__all__ = [
    "Movie", "MovieCollection",
    "DataLoader", "CSVLoader", "JSONLoader", "TMDBLoader",
    "BaseAnalyzer", "GenreAnalyzer", "TrendAnalyzer", "FinancialAnalyzer",
    "SuccessPredictor",
    "UserPreference",
    "Recommendation", "BaseRecommender", "ContentRecommender",
    "SimilarityRecommender", "PopularityRecommender",
    "BaseExplainer", "RuleExplainer", "AIExplainer", "build_explainer",
    "MovieDataError", "InvalidBudgetError", "InvalidGrossError",
    "MovieNotFoundError", "ModelNotTrainedError", "DataFileError",
    "InvalidPreferenceError", "AIServiceError",
]
