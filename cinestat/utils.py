"""Small helpers shared by the rest of the package.

Syllabus topics demonstrated here:
  Class 9  - context manager (__enter__ / __exit__), File I/O, pathlib
  Class 11 - functions as objects, decorators
"""

import csv
import json
import time
import functools
import warnings
from contextlib import contextmanager
from pathlib import Path

from .exceptions import DataFileError


# ---------------------------------------------------------------------------
# Class 11: a DECORATOR
# ---------------------------------------------------------------------------
def timed(func):
    """Print how long a function took, then return its result unchanged.

    A decorator is just a function that takes another function and returns a
    new one. Use it by writing @timed on the line above a function.

        @timed
        def analyze(self): ...
    """

    @functools.wraps(func)          # keeps the original name and docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[timed] {func.__name__} took {elapsed_ms:.1f} ms")
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Class 9: a CONTEXT MANAGER
# ---------------------------------------------------------------------------
class ExportSession:
    """Writes a list of dictionaries to a .csv or .json file.

    Used with the `with` keyword, which guarantees the file is closed even
    if an error happens half way through:

        with ExportSession("exports/horror.csv") as export:
            export.write(rows)
    """

    def __init__(self, path):
        self.path = Path(path)
        self.rows_written = 0
        self._file = None

    def __enter__(self):
        """Runs when the `with` block starts. Whatever we return becomes
        the variable after `as`."""
        # Create the folder if it does not exist yet (pathlib).
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._file = open(self.path, "w", newline="", encoding="utf-8")
        except OSError as error:
            raise DataFileError(f"Could not open {self.path}: {error}")
        return self

    def write(self, rows):
        """Write the rows in the format matching the file extension."""
        rows = list(rows)
        if not rows:
            return 0

        if self.path.suffix.lower() == ".json":
            json.dump(rows, self._file, indent=2)
        else:
            writer = csv.DictWriter(self._file, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        self.rows_written = len(rows)
        return self.rows_written

    def __exit__(self, exc_type, exc_value, traceback):
        """Runs when the `with` block ends - even if an error was raised."""
        if self._file is not None:
            self._file.close()
        # Returning False means "do not hide any error that happened".
        return False


# ---------------------------------------------------------------------------
# A second context manager, this one for hiding a misleading warning
# ---------------------------------------------------------------------------
@contextmanager
def quiet_blas_warning():
    """Hide one specific false alarm printed by numpy on macOS.

    On macOS, numpy uses Apple's "Accelerate" maths library, which sometimes
    prints "divide by zero encountered in matmul" during a completely normal
    multiplication. We checked this carefully: the numbers going in and the
    answers coming out are all valid, and they match a hand-calculated result
    exactly. So the warning is wrong and only confuses the user.

    On Windows, numpy uses OpenBLAS instead and the warning never appears, so
    this does nothing at all there. It is kept because the same source runs on
    both, and because a `with` block that filters a warning nobody raised costs
    nothing - the wrong fix would be to delete it and rediscover the bug on the
    next Mac the project is opened on.

    We hide ONLY that one message, and only for the lines inside the `with`
    block - every other warning still gets through.

    Written with @contextmanager, which is a shorter way of building a context
    manager than writing __enter__ and __exit__ by hand (compare ExportSession).
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore",
                                message=".*encountered in matmul.*",
                                category=RuntimeWarning)
        yield


# ---------------------------------------------------------------------------
# Plain formatting helpers
# ---------------------------------------------------------------------------
def money(value):
    """Turn 138400000 into '$138.4M' so tables stay readable."""
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.0f}K"
    return f"{sign}${value:.0f}"
