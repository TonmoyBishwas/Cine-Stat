"""Start the CineStat application.

Run it from the project folder with:

    python main.py                      # the dataset that ships with the repo
    python main.py data/tmdb.csv        # the big Kaggle dataset, if you have it

The loader is chosen automatically from the file's columns, so the same
command works for either one. See README.md, "Using the bigger dataset".
"""

import sys
from pathlib import Path

from cinestat.gui import MovieApp

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "movies.csv"


def main():
    # sys.argv holds the words typed after "python". argv[0] is the script
    # name, so argv[1] - if it is there at all - is the data file.
    data_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA
    app = MovieApp(data_file)
    app.mainloop()          # hands control to Tkinter and waits for clicks


if __name__ == "__main__":
    main()
