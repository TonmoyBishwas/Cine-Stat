"""Start the CineStat application.

Run it from the project folder with:

    python main.py
"""

from pathlib import Path

from cinestat.gui import MovieApp

DATA_FILE = Path(__file__).resolve().parent / "data" / "movies.csv"


def main():
    app = MovieApp(DATA_FILE)
    app.mainloop()          # hands control to Tkinter and waits for clicks


if __name__ == "__main__":
    main()
