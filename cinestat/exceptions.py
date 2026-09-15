"""Custom exception classes.

Syllabus Class 9: custom exceptions.

Every error CineStat raises inherits from MovieDataError. That means a caller
who does not care about the exact problem can catch them all at once:

    try:
        ...
    except MovieDataError as e:
        print("Something went wrong:", e)
"""


class MovieDataError(Exception):
    """Base class for every error raised by CineStat."""


class InvalidBudgetError(MovieDataError):
    """Raised when a budget is negative or is not a number."""


class InvalidGrossError(MovieDataError):
    """Raised when a gross (revenue) value is negative or not a number."""


class MovieNotFoundError(MovieDataError):
    """Raised when a movie title is not present in the collection."""


class ModelNotTrainedError(MovieDataError):
    """Raised when predict() is called before train()."""


class DataFileError(MovieDataError):
    """Raised when a data file is missing or cannot be read."""


class InvalidPreferenceError(MovieDataError):
    """Raised when a UserPreference is given a value that makes no sense.

    For example a minimum IMDb score of 15 (the scale only goes to 10), or a
    year range that ends before it starts.
    """


class AIServiceError(MovieDataError):
    """Raised when the OpenRouter AI service cannot be reached or refuses us.

    It inherits from MovieDataError like every other CineStat error, so the
    GUI can keep catching one exception type and show one kind of dialog.
    """
