# 4. OOP explained, with this project as the example

[← how it fits together](03-how-it-all-fits-together.md) · [back to index](README.md) · [next: the Windows version →](05-the-windows-version.md)

---

This page explains every object-oriented idea the course covers, in plain
English, and then points at exactly where it lives in this project.

Each one follows the same three-step shape:

> **What it means** → **Why anyone bothers** → **Where it is here**

---

## First, the one-paragraph version of OOP

If you come from data analysis, you are used to *data in one place* (a
DataFrame) and *functions in another* (your notebook cells). You pass the data
to the functions.

Object-oriented programming keeps the data and the functions that work on it
**in the same box**. A `Movie` is not just numbers; it is numbers that know how
to check themselves, work out their own profit, and compare themselves to
another film.

That is the whole idea. Everything below is a refinement of it.

---

## 1. Classes and objects

**What it means.** A **class** is the blueprint. An **object** is one thing
built from that blueprint. `Movie` is the blueprint; *Titanic* is an object.

**Why anyone bothers.** You describe "what a film is" once, and then make 5,418
of them.

**Where it is here.** `cinestat/movie.py`:

```python
class Movie:                      # the blueprint
    def __init__(self, name, year, ...):   # the constructor
        self.name = str(name)     # an instance variable
        self.year = int(year)
```

`__init__` is the **constructor** — it runs automatically every time you write
`Movie(...)`. `self.name` is an **instance variable**: every film has its own.

*Syllabus Class 2.*

---

## 2. Encapsulation (and "private" attributes)

**What it means.** Keeping some of an object's data protected, so the outside
world has to go through a check to change it.

**Why anyone bothers.** A film with a negative budget is nonsense. Rather than
hoping nobody ever writes one, the class makes it *impossible*.

**Where it is here.** `movie.py` stores budget as `__budget` — two underscores.
Python then secretly renames it to `_Movie__budget`, which is called **name
mangling**. Code outside the class cannot reach it by accident.

To read and write it you go through a **property**, which looks like a normal
attribute but is really a method:

```python
film.budget = -5        # raises InvalidBudgetError
film.budget = 1000000   # fine - and it was checked on the way in
```

The nice part: the person using the class writes `film.budget` exactly as if it
were an ordinary variable. The protection is invisible and free.

**Also in** `preferences.py`, which protects `__genres`, `__ratings` and
`__min_score` the same way — a minimum IMDb score of 15 is rejected, because
the scale stops at 10.

*Syllabus Class 3.*

---

## 3. Static vs instance members

**What it means.** Some things belong to **one object**; some belong to **the
whole class**.

**Why anyone bothers.** "What counts as a hit?" is not a property of any one
film — it is a rule for all of them.

**Where it is here.** In `movie.py`:

| | Belongs to | Example |
|---|---|---|
| Instance variable | one film | `self.name`, `self.budget` |
| Class variable | every film | `Movie.count`, `Movie.HIT_RATIO = 2.0` |

`Movie.count` counts how many films have ever been created. `Movie.HIT_RATIO`
is the 2× rule. Change `HIT_RATIO` once and every film in the project re-judges
itself — including the Predict tab's verdict.

*Syllabus Class 3.*

---

## 4. Composition — "has-a"

**What it means.** One object **contains** another. A car *has an* engine.

**Why anyone bothers.** It is the simplest way to build something bigger out of
something smaller, and it is usually the right answer when you are tempted to
use inheritance.

**Where it is here.**

- `MovieCollection` **has a** list of `Movie` objects (`collection.py`)
- `AIExplainer` **has a** `RuleExplainer` inside it, to fall back on
- *(Windows branch)* `WindowsTheme` **has a** `Palette`

A `MovieCollection` does not *inherit* from `Movie` — a library is not a kind
of book, it is a thing that **holds** books. Getting that distinction right is
worth a mark.

*Syllabus Class 3.*

---

## 5. Inheritance and method overriding

**What it means.** A child class gets everything the parent has, and can
replace any part it wants to do differently.

**Why anyone bothers.** Write the shared 90% once; write only the 10% that
differs.

**Where it is here.** `loaders.py` is the clearest example:

```
DataLoader                     the parent - writes all the cleaning steps
   ├── CSVLoader               only replaces load():  pd.read_csv
   ├── JSONLoader              only replaces load():  pd.read_json
   └── TMDBLoader              replaces load() with chunked reading
```

All the cleaning — dropping bad rows, extracting the month, calculating profit
and ROI, grouping rare genres — is written **once** in the parent and inherited
by all three. Each child replaces only `load()`. That replacing is **method
overriding**.

**Also:** `BaseAnalyzer` → three analyzers; `BaseRecommender` → three
recommenders; `BaseExplainer` → two explainers; `BaseTab` → five tabs.

*Syllabus Class 4.*

---

## 6. Abstraction (abstract base classes)

**What it means.** A parent that says *"every child must have this method"* but
refuses to say how. You cannot create the parent itself.

**Why anyone bothers.** It turns "please remember to write a `load()` method"
into a rule the computer enforces. Forget it and the program refuses to build
the class at all — at once, loudly, instead of failing mysteriously later.

**Where it is here.** Four of them:

| Abstract parent | Demands | Children |
|---|---|---|
| `DataLoader` | `load()` | CSV, JSON, TMDB |
| `BaseAnalyzer` | `analyze()`, `summary()` | Genre, Trend, Financial |
| `BaseRecommender` | `score_movie()` | Content, Similarity, Popularity |
| `BaseExplainer` | `explain()` | Rule, AI |

```python
DataLoader("file.csv")     # TypeError - it is abstract, you cannot build it
CSVLoader("file.csv")      # fine
```

*Syllabus Class 4.*

---

## 7. Polymorphism

**What it means.** "Many shapes." Different objects respond to the **same
instruction** in their own way — and the code giving the instruction does not
need to know which one it has.

**Why anyone bothers.** This is what lets you add a fourth analyzer without
editing anything that uses analyzers.

**Where it is here.** Everywhere. The clearest:

```python
for analyzer in [GenreAnalyzer(movies),
                 TrendAnalyzer(movies),
                 FinancialAnalyzer(movies)]:
    analyzer.report()          # same call, three different calculations
```

The loop has no idea which one it is holding.

**And the one that does real work in the app:**

```python
engine = self.ENGINES[self.engine_box.get()]   # whichever the user picked
suggestions = engine(self.movies, profile).recommend(15)
```

The Recommend tab genuinely does not know whether it is holding a
`ContentRecommender`, a `SimilarityRecommender` or a `PopularityRecommender`.
All three answer `.recommend()`. **Adding a fourth means adding one name to one
list** — the dropdown menu picks it up by itself.

The same is true of the two explainers: the GUI holds a variable called
`explainer`, calls `explainer.explain(...)`, and cannot tell whether the answer
came from our own code or from an AI.

*Syllabus Class 5.*

---

## 8. Operator overloading (dunder methods)

**What it means.** Teaching your own class what `+`, `>`, `==`, `len()` and
`for ... in` should mean for it. The methods have double underscores, so people
call them "dunder" methods.

**Why anyone bothers.** Code that reads like English instead of like plumbing.

**Where it is here.**

On `Movie`:

| You write | It runs | It means |
|---|---|---|
| `print(film)` | `__str__` | a readable line |
| `film_a == film_b` | `__eq__` | same title and year |
| `film_a > film_b` | `__gt__` | bigger box office |
| `sorted(films)` | `__lt__` | order by box office |

On `MovieCollection`:

| You write | It runs |
|---|---|
| `len(movies)` | `__len__` |
| `for film in movies` | `__iter__` |
| `movies[0]` | `__getitem__` |
| `film in movies` | `__contains__` |
| `movies_a + movies_b` | `__add__` |

**The best example in the project** is in the Compare tab. To decide which film
did better it writes:

```python
if first > second:
    winner, loser = first, second
```

Not `first.gross > second.gross`. The meaning of `>` was defined once in
`movie.py`, and now the tab reads like a sentence.

On `UserPreference`, `film in profile` means *"I ticked this one"*. On
`Recommendation`, `__lt__` is what makes `sorted()` rank suggestions.

*Syllabus Class 5.*

---

## 9. Multiple inheritance

**What it means.** A class with two parents.

**Where it is here.** Twice:

```python
class FinancialAnalyzer(BaseAnalyzer, ExportMixin):
class BaseTab(ttk.Frame, ABC):
```

`FinancialAnalyzer` **is an** analyzer **and** it can export itself.
`ExportMixin` is a **mixin** — a small class whose only purpose is to lend one
ability to another class.

`BaseTab` is both a rectangle of the window (`ttk.Frame`) and an abstract class
(`ABC`) that forces every tab to write `build_ui()`.

*Syllabus Class 5.*

---

## 10. The factory method

**What it means.** A method whose job is to decide **which class to build**, so
the caller does not have to.

**Why anyone bothers.** The caller says what it wants, not how to get it.

**Where it is here.** `DataLoader.for_file()` in `loaders.py`. It opens the
file, reads the first line, looks at the column names, and returns whichever of
the three loaders is correct:

```python
movies = DataLoader.for_file("data/movies.csv").to_collection()   # CSVLoader
movies = DataLoader.for_file("data/tmdb.csv").to_collection()     # TMDBLoader
```

Both lines work, and **nothing downstream can tell the difference**.

*Syllabus Class 4.*

---

## 11. The template method

**What it means.** The parent writes down the **steps**, in order, and leaves
one of them blank for the children to fill in.

**Where it is here.** `BaseRecommender.recommend()`. Every recommendation
follows the same four steps — filter, score, sort, cut. Only *score* differs.
So the parent writes:

```python
for movie in self.candidates():          # step 1, written once
    score, reasons = self.score_movie(movie)   # step 2 - the child's job
    ...
results.sort(reverse=True)               # step 3, written once
return results[:n]                       # step 4, written once
```

A new recommender writes **one method** and inherits the other three steps.

*Syllabus Class 4.*

---

## 12. Duck typing

**What it means.** *"If it walks like a duck and quacks like a duck, treat it
as a duck."* Python does not ask what class something is — only whether it can
do what is being asked.

**Where it is here.** `MovieApp.active_tab()`. The File → Export menu exports
whichever tab is open. It does not check types. It just asks: *does this tab
have a `current_rows()` method?*

Browse and Recommend both do, so both can be exported — **with no shared base
class needed for it**. Give a sixth tab that method tomorrow and export works
on it immediately.

*Syllabus Class 5.*

---

## 13. Custom exceptions

**What it means.** Your own error types, arranged in a family tree.

**Where it is here.** `exceptions.py` — seven of them, all descended from
`MovieDataError`, which means one `except` catches them all.

Used for real: type letters into the budget box in the Predict tab and you get
a polite dialog, not a crash. There is a test for exactly that.

*Syllabus Class 9.*

---

## 14. Context managers (`with`)

**What it means.** An object that runs setup when a block starts and **cleanup
when it ends — even if something goes wrong in the middle**.

**Where it is here.** `ExportSession` in `utils.py`:

```python
with ExportSession("exports/horror.csv") as export:
    export.write(rows)
```

The file is closed properly whether the write succeeded or blew up. It is
written the long way (`__enter__` / `__exit__`) so you can see the machinery.

`quiet_blas_warning()` in the same file is a second one, written the short way
with `@contextmanager`. And `TMDBLoader` uses `with pd.read_csv(chunksize=...)`
to guarantee the huge file gets closed even if reading stops early.

*Syllabus Class 9.*

---

## 15. Decorators

**What it means.** A function that wraps another function to add behaviour,
without editing the original.

**Where it is here.** `@timed` in `utils.py`, used on `BaseAnalyzer.run()` and
`BaseRecommender.recommend()`:

```python
@timed
def run(self):
    ...
```

Every analysis now prints how long it took, and **not one line inside `run()`
changed**. Remove the `@timed` line and the timing disappears just as cleanly.

`@property`, `@classmethod`, `@abstractmethod` and `@staticmethod` are
decorators too — used all over the project.

*Syllabus Class 11.*

---

## 16. Iterators and generators

**What it means.** A generator produces results **one at a time, as you ask for
them**, instead of building the whole list up front. You write `yield` instead
of `return`.

**Why anyone bothers.** Memory. And the ability to stop early.

**Where it is here.** `collection.py` — `filter_by()`, `search()` and
`in_year_range()` all `yield`. `recommenders.py` — `candidates()` yields the
films eligible to be suggested.

`MovieCollection.__iter__` is the **iterator** that makes
`for film in movies:` work.

*Syllabus Class 11.*

---

## 17. Functions as objects

**What it means.** In Python a function is a value. You can store it in a
dictionary.

**Where it is here.** `charts_tab.py` maps a chart's name to **the method that
draws it**:

```python
self.charts = {
    "Average box office by genre": self.chart_gross_by_genre,
    "Return on investment by genre": self.chart_roi_by_genre,
    ...
}
```

The dropdown is built from the keys, and drawing is one line:
`self.charts[chosen](axes)`. **Adding a ninth chart means adding one line and
one method** — the menu updates itself.

`recommend_tab.py` does the same, but maps a menu label to a **class**.

*Syllabus Class 11.*

---

## 18. Multithreading

**What it means.** Doing two things at once, so a slow job does not freeze
everything else.

**Where it is here.** `recommend_tab.py`. The AI call takes seconds. On the
thread that draws the window, that would freeze the program — indistinguishable
from a crash.

So the request runs on a **second thread**, and the answer comes back through a
`queue.Queue`.

**The golden rule, worth quoting:** only the main thread may touch anything
belonging to Tkinter. So the worker thread touches nothing on screen. It puts
its answer in the queue; the main thread checks that queue every 100 ms.

*Syllabus Class 12.*

---

## 19. Modules, packages and testing

**What it means.** A **module** is one `.py` file; a **package** is a folder of
them with an `__init__.py`.

**Where it is here.** `cinestat/` and `cinestat/gui/` are both proper packages.
`tests/` holds **300 unittest tests**.

*Syllabus Class 10.*

---

## 20. MVC-lite — separating the interface from the logic

**What it means.** Keep what the program *knows* apart from how it *looks*.

**Where it is here.** The rule from
[page 3](03-how-it-all-fits-together.md): `cinestat/gui/` may use `cinestat/`;
`cinestat/` never uses `cinestat/gui/`.

The proof that it works: the same analysis classes are used by a Jupyter
notebook with no window at all, and by a five-tab desktop application. Neither
knows about the other.

*Syllabus Class 8.*

---

## The one-page cheat sheet

| Idea | Best example in this project |
|---|---|
| Class, object, constructor | `Movie` — `movie.py` |
| Encapsulation, name mangling | `Movie.__budget` behind a validating property |
| Static vs instance members | `Movie.count` and `Movie.HIT_RATIO` vs `self.name` |
| Composition | `MovieCollection` *has a* list of `Movie`s |
| Inheritance, overriding | `DataLoader` → `CSVLoader`, `JSONLoader`, `TMDBLoader` |
| Abstraction (ABC) | `BaseAnalyzer`, `BaseRecommender`, `BaseExplainer`, `DataLoader` |
| Polymorphism | three analyzers, three recommenders, two explainers |
| Operator overloading | `film_a > film_b` in the Compare tab |
| Multiple inheritance | `FinancialAnalyzer(BaseAnalyzer, ExportMixin)` |
| Factory method | `DataLoader.for_file()` |
| Template method | `BaseRecommender.recommend()` |
| Duck typing | `active_tab()` exporting anything with `current_rows()` |
| Custom exceptions | `MovieDataError` and its six children |
| Context manager | `ExportSession` |
| Decorator | `@timed` |
| Generators | `filter_by()`, `search()`, `candidates()` |
| Functions as objects | `ChartsTab.charts` |
| Multithreading | the AI call in `recommend_tab.py` |
| Packages and testing | `cinestat/`, `cinestat/gui/`, 300 tests |
| MVC-lite | the core never imports the interface |

---

[← how it fits together](03-how-it-all-fits-together.md) · [back to index](README.md) · [next: the Windows version →](05-the-windows-version.md)
