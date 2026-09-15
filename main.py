"""Start the CineStat application.

Windows, from a terminal opened in the project folder:

    py main.py                          the dataset that ships with the repo
    py main.py data\\tmdb.csv             the big Kaggle dataset, if you have it

or just double-click **run.bat**, which does the same thing and keeps the
window open if anything goes wrong.

`py` is the Python launcher that the official Windows installer puts on the
PATH; `python` works too if that is what is on yours. On macOS and Linux the
command is `python3 main.py` - everything below this line is the same either
way.

The loader is chosen automatically from the file's columns, so the same
command works for either dataset. See README.md, "Using the bigger dataset".
"""

import sys
from pathlib import Path

from cinestat.gui import MovieApp

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "movies.csv"


def main():
    # sys.argv holds the words typed after "python". argv[0] is the script
    # name, so argv[1] - if it is there at all - is the data file.
    data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA

    if not data_file.exists():
        # Worth catching here rather than inside the window: a message box
        # that appears and vanishes behind a traceback helps nobody, and on
        # Windows the usual cause is running the command from the wrong
        # folder, which the printed path makes obvious.
        print(f"Could not find the data file:\n    {data_file}\n")
        print("Run this from the project folder, where data\\movies.csv lives,")
        print("or pass the path to a data file:  py main.py path\\to\\movies.csv")
        return 1

    app = MovieApp(data_file)
    app.mainloop()          # hands control to Tkinter and waits for clicks
    return 0


if __name__ == "__main__":
    sys.exit(main())
