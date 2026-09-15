# 7. Glossary

[← questions you might get asked](06-questions-you-might-get-asked.md) · [back to index](README.md)

---

Every technical word used in this project, in one or two lines, with where it
appears.

---

## Object-oriented words

| Word | What it means | Where in this project |
|---|---|---|
| **Class** | A blueprint for making objects | `Movie` |
| **Object / instance** | One thing built from a class | *Titanic* |
| **Constructor** (`__init__`) | The method that runs when an object is made | `Movie.__init__` |
| **Instance variable** | Data belonging to one object | `self.name` |
| **Class variable** | Data shared by every object of the class | `Movie.HIT_RATIO` |
| **Method** | A function that belongs to a class | `movie.to_dict()` |
| **Encapsulation** | Protecting data behind checks | `Movie.__budget` |
| **Name mangling** | Python renaming `__x` to `_Class__x` to hide it | `__budget` → `_Movie__budget` |
| **Property** | A method that looks like an attribute | `movie.budget` |
| **Inheritance** | A child class getting the parent's abilities | `CSVLoader(DataLoader)` |
| **Overriding** | A child replacing a parent's method | `CSVLoader.load()` |
| **Multiple inheritance** | A class with two parents | `FinancialAnalyzer(BaseAnalyzer, ExportMixin)` |
| **Mixin** | A small class that lends one ability | `ExportMixin` |
| **Composition** | One object containing another ("has-a") | `MovieCollection` has a list of `Movie`s |
| **Abstract class (ABC)** | A parent that cannot be built, only inherited | `DataLoader` |
| **Abstract method** | A method a child *must* write | `DataLoader.load()` |
| **Polymorphism** | Same call, different behaviour underneath | three analyzers, one `.report()` |
| **Duck typing** | Caring what an object *can do*, not what it *is* | `active_tab()` and `current_rows()` |
| **Dunder method** | A `__name__` method Python calls for you | `__len__`, `__gt__` |
| **Operator overloading** | Teaching your class what `>` or `+` mean | `film_a > film_b` |
| **Class method** | A method on the class, often a second constructor | `UserPreference.from_movies()` |
| **Factory method** | A method that decides which class to build | `DataLoader.for_file()` |
| **Template method** | Parent writes the steps, child fills one in | `BaseRecommender.recommend()` |
| **Decorator** | A function that wraps another to add behaviour | `@timed` |
| **Context manager** | An object that guarantees cleanup after `with` | `ExportSession` |
| **Generator** | A function that `yield`s results one at a time | `collection.search()` |
| **Iterator** | The thing that makes `for x in y` work | `MovieCollection.__iter__` |
| **Exception** | An error object that can be caught | `InvalidBudgetError` |
| **Module** | One `.py` file | `movie.py` |
| **Package** | A folder of modules with `__init__.py` | `cinestat/` |
| **MVC-lite** | Keeping the interface separate from the logic | `gui/` never calculates |

---

## Data and statistics words

| Word | What it means | Where |
|---|---|---|
| **DataFrame** | A pandas table | `collection.to_dataframe()` |
| **ROI** | Return on investment: box office ÷ budget | `movie.roi` |
| **Gross** | Total box-office takings, before costs | `movie.gross` |
| **Profit** | Gross minus budget | `movie.profit` |
| **Correlation** | How strongly two numbers move together, −1 to +1 | budget ↔ gross = 0.74 |
| **Linear regression** | Fitting a straight-line relationship | `SuccessPredictor` |
| **R²** | How much of the variation the model explains, 0 to 1 | 0.588 |
| **MAE** | Mean absolute error — average miss, in dollars | ~$67M |
| **One-hot encoding** | Turning words into 0/1 columns | genre → `genre_group_Action` |
| **Feature scaling** | Putting every column on the same scale | `StandardScaler` |
| **Train/test split** | Holding films back to test honestly | 80% train, 20% test |
| **Data leakage** | Using information that would not exist yet | why `score` is excluded |
| **Baseline** | A deliberately simple comparison | budget-only model; popularity recommender |
| **Median vs mean** | Middle value vs average | ROI uses median — outliers |
| **Ill-conditioned** | Numbers so different in size the maths breaks | the model bug |

---

## Interface and Windows words

| Word | What it means | Where |
|---|---|---|
| **Tkinter** | Python's built-in windows-and-buttons library | all of `gui/` |
| **ttk** | The newer, better-looking half of Tkinter | `ttk.Treeview` |
| **Widget** | Any one interface piece: button, table, box | `MoviePicker` |
| **Treeview** | ttk's table widget | the Browse table |
| **Notebook** | ttk's tabbed container | the five tabs |
| **Callback** | A function run when something is clicked | `command=self.predict` |
| **Event loop** | The endless "wait for a click" cycle | `app.mainloop()` |
| **Thread** | A second line of execution, so nothing freezes | the AI call |
| **Queue** | A safe letterbox between two threads | `self._ai_replies` |
| **DPI** | Dots per inch — screen sharpness | `platform_ui.screen_scale()` |
| **DPI awareness** | Telling Windows "I'll scale myself" | `SetProcessDpiAwareness` |
| **ttk theme** | The set of rules for drawing widgets | `clam` |
| **Palette** | One object holding one look's colours | `LIGHT`, `DARK` |
| **Accent colour** | The colour the user chose in Windows Settings | the blue buttons |
| **Registry** | Where Windows stores its settings | reading dark mode |
| **ctypes** | Calling Windows' own functions from Python | `platform_ui.py` |
| **Mnemonic** | The underlined letter Alt reaches | Alt+F for File |
| **Accelerator** | The shortcut text shown in a menu | `Ctrl+E` |

---

## Project-specific words

| Word | What it means |
|---|---|
| **Verdict** | Hit (≥2× budget), Break-even (≥1×), or Flop |
| **Taste profile** | What `UserPreference` infers from ticked films |
| **Match score** | A recommendation's mark out of 100 |
| **Reasons** | The plain-English notes recorded as each point is given |
| **Seed film** | The single film `SimilarityRecommender` compares against |
| **Genre group** | Genre with rare ones merged into "Other" |
| **The core** | `cinestat/` — everything that thinks |
| **The interface** | `cinestat/gui/` — everything that draws |

---

## File-extension words

| Word | What it means |
|---|---|
| **`.env`** | A file holding secrets, never committed to GitHub |
| **`.gitignore`** | The list of files Git must ignore |
| **`.gitattributes`** | Rules for how Git treats files (line endings) |
| **`.bat`** | A Windows script — `run.bat`, `setup.bat` |
| **`.ico`** | A Windows icon file |
| **`.ipynb`** | A Jupyter notebook |
| **`.venv`** | A private folder of this project's Python packages |

---

[← questions you might get asked](06-questions-you-might-get-asked.md) · [back to index](README.md)
