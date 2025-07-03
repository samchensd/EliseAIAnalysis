# EliseAI Calendar Analysis

This repository contains a small data analysis project for examining agent travel schedules. The scripts load an Excel workbook, build a SQLite database, and produce metrics on travel time, lateness risk, and potential optimizations.

## Directory Overview
- `data/` – input materials including the example Excel file and cached property coordinates.
- `src/` – core analysis modules:
  - `data_loading.py` – reads the Excel workbook and creates the SQLite database.
  - `travel_analysis.py` – computes travel times and distances between properties.
  - `optimization.py` – a simple insertion heuristic that estimates schedule improvements.
  - `agent_specialization.py` – measures how focused each agent is on specific properties.
  - `lateness_analysis.py` – identifies transitions that are at risk of being late.
  - `visualization.py` – helper functions for plotting.
- `main.py` – runs a full analysis using the modules above.
- `db_explorer.py` and `quick_analysis.py` – utilities for inspecting the generated database and previously saved results.

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the main analysis:
   ```bash
   python main.py
   ```
   The script reads `data/Agent Calendar Practical Materials.xlsx` and generates summary reports.

## Notes
Generated output files and logs have been removed from the repository and are ignored via `.gitignore`.
