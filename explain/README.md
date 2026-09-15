# CineStat, explained

These notes exist so that anyone can sit down, read for twenty minutes, and
then confidently explain what every file in this project does and why it is
there.

They assume you are comfortable with Python and with data analysis — you know
what a DataFrame is, you have used `groupby`, you understand a regression.
They do **not** assume you are comfortable with object-oriented programming.
That is the part these notes teach, using this project as the example.

---

## Read them in this order

| # | File | What it covers | Time |
|---|---|---|---|
| 1 | **[What the project does](01-what-the-project-does.md)** | The idea, the data, the two halves, the findings | 5 min |
| 2 | **[The files, one by one](02-the-files-one-by-one.md)** | Every Python file: what it does, in plain English | 10 min |
| 3 | **[How it all fits together](03-how-it-all-fits-together.md)** | Following one button click through the whole program | 5 min |
| 4 | **[OOP explained with this project](04-oop-explained.md)** | Every OOP idea, with the real example from this code | 10 min |
| 5 | **[The Windows version](05-the-windows-version.md)** | What the `windows` branch adds and why | 5 min |
| 6 | **[Questions you might get asked](06-questions-you-might-get-asked.md)** | Likely viva questions, with answers | 10 min |
| 7 | **[Glossary](07-glossary.md)** | Every technical word, in one line each | look up as needed |

If you only have five minutes before you have to speak, read the box below and
then jump to **[Questions you might get asked](06-questions-you-might-get-asked.md)**.

---

## The whole project in one box

> CineStat reads 40 years of film data and answers two questions: **what makes
> a film make money**, and **what should I watch next?**
>
> It is built in **two layers**. The bottom layer (`cinestat/`) does all the
> thinking — reading the data, the statistics, the prediction model, the
> recommendations. The top layer (`cinestat/gui/`) is the window you click on.
>
> The top layer never calculates anything. It asks the bottom layer for
> answers and draws them. That one rule is what makes the project tidy, and it
> is the thing most worth pointing at.
>
> The same bottom layer is used **twice**: once by a Jupyter notebook (Part 1)
> and once by the desktop app (Part 2). The analysis is written once and used
> in both places. Nothing is copied and pasted.

---

## The shape of it

```
                    data/movies.csv
                          |
                   [ loaders.py ]          reads and cleans the file
                          |
                   [ movie.py ]            one film = one object
                          |
                 [ collection.py ]         all the films together
                          |
          +---------------+---------------+
          |               |               |
   [ analyzers.py ] [ predictor.py ] [ recommenders.py ]
    the statistics   the prediction    the suggestions
          |               |               |
          +---------------+---------------+
                          |
              +-----------+-----------+
              |                       |
     the Jupyter notebook      the desktop app
          (Part 1)            ( cinestat/gui/ )
                                   (Part 2)
```

Everything flows **upward**. The bottom of that diagram never knows the top
exists — `movie.py` has no idea whether it is being used by a notebook or by a
window, and that is deliberate.

---

## Honest notes

Three things in this project are deliberately reported rather than hidden,
because a project that admits its limits is stronger than one that does not.
All three are explained in full in
[Questions you might get asked](06-questions-you-might-get-asked.md):

1. **The prediction model is 59% accurate, and that is the honest ceiling.**
   The rest is the script, the cast, the marketing and luck.
2. **Budget does almost all of the predictive work.** Genre, age rating and
   release month together add less than 0.01 to the score. We report the
   budget-only model right next to the full one.
3. **The AI does not choose the recommendations.** Our own code chooses them
   and works out why. The AI is handed those reasons and asked to write them
   up nicely. Unplug the internet and the feature still works.

---

## Where the numbers in these notes come from

Every figure quoted in these notes was produced by running the real code on
the real dataset, not copied from an older draft. If you change the data or
the model, re-check them with:

```bat
py -c "from cinestat import CSVLoader, SuccessPredictor; m = CSVLoader('data/movies.csv').to_collection(); p = SuccessPredictor(m); print(len(m), p.train(), p.budget_only_r2())"
```
