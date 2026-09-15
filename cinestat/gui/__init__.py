"""The Tkinter user interface for CineStat.

Keeping the interface in its own sub-package is the "MVC-lite" idea from
Syllabus Class 8: the windows and buttons live in here, while all the data
handling and maths live in the cinestat package next door. The tabs ask the
analysis classes for answers; they never work out the answers themselves.
"""

from .app import MovieApp

__all__ = ["MovieApp"]
