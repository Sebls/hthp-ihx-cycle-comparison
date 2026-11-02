# High-Temperature Heat Pump Cycle Comparison

Compare a baseline high-temperature heat pump cycle (S0) with the assigned
advanced cycle (S1-S5), evaluate performance, and run parametric studies.

This repository is a starting scaffold. Neither cycle is implemented yet, and
`report/report.pdf` is a compiled report template, not a completed analysis.
Select the assigned advanced cycle and obtain the operating conditions and
shared course library before implementing the model.

## Repository structure

```text
project/
├── main.py
├── report/
│   ├── report.tex
│   ├── report.pdf
│   └── figures/
├── requirements.txt
├── README.md
└── .gitignore
```

All model code, performance calculations, parametric analyses, and figure
generation belong in `main.py`. Store generated plots and cycle diagrams in
`report/figures/`. Keep the final report within 10 pages.

## Installation

Use Python 3.10 or newer. From this repository directory:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Dependencies are CoolProp, NumPy, and Matplotlib. Add the shared course library
to `requirements.txt` if required and available as an installable package.

## Run the model

```sh
python main.py
```

Currently this creates the figure directory and prints the scaffold status.
The cycle functions explicitly raise `NotImplementedError` until implemented.
Replace the status-only execution with the cycle comparison and parameter
sweeps when the model is ready.

## Build the report

Install a LaTeX distribution with `pdflatex`, then run:

```sh
cd report
pdflatex -interaction=nonstopmode -halt-on-error report.tex
pdflatex -interaction=nonstopmode -halt-on-error report.tex
```

The output is `report/report.pdf`. Temporary LaTeX files are ignored by Git;
the report PDF and generated figures can be committed.

## Git

This directory is an independent Git repository nested in `energy-systems`.
Run Git commands from here (or use `git -C project` from the parent directory).
No remote or initial commit is configured.
