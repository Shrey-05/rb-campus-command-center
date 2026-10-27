# RB Campus Command Center

A Streamlit dashboard I built to run Red Bull's campus activation program across 5+ campuses in Hyderabad. It replaced chasing status across three messy Excel trackers with a single view of what is on track, what is at risk, who owns what, and which activation formats are worth repeating.

> **Note on data:** The source trackers are internal Red Bull files, so no data is included in this repo. The code is published to show how the tool works. See [Running it](#running-it) for the expected data layout.

## What it does

The app reads cleaned CSVs and exposes five pages from a sidebar.

| Page | What it answers |
|---|---|
| **Overview Dashboard** | How many activations are planned, and what is the status of each (On Track, At Risk, Needs Follow-Up, Incomplete Data)? |
| **Risk & Prioritization** | Which Tier A/B festivals need attention first? Highlights festivals lost to competition and those with competitor activity noted. |
| **Owner / Blocker Log** | Who owns which activations, and what is overdue? Flags any owner with 2+ activations needing follow-up. |
| **ROI Recommendation Engine** | Cost per can sold and cost per attendee for each third-party event, with a recommendation on which formats to deprioritize. |
| **Weekly Review Summary** | A one-click weekly summary for operational reviews, exportable as Markdown or plain text. |

A date picker in the sidebar lets you change "today" to see how statuses shift without changing any underlying data.

## How the logic works

- **Rule-based status:** each activation is labelled by simple, readable rules, for example *At Risk* means the activation is within 5 days and assets or budget are still blank, and *Needs Follow-Up* means the date has passed.
- **Blocker aging:** overdue items are grouped by owner so stalled work surfaces early in reviews.
- **Transparent ROI math:** cost per can and cost per attendee are plain division. There is no machine learning. Events with missing cost or sales data are excluded from a calculation rather than guessed at.
- **Honest missing data:** unknown values are labelled `Unknown` or `Incomplete Data`, never silently filled in.

## Data pipeline

```
data/raw/*.xlsx  ->  clean_data.py  ->  data/clean/*.csv  ->  app.py
```

`clean_data.py` reads three raw Excel trackers (a freshers campaign sheet, a festival tracker, and a third-party events sheet) and:

- drops blank padding rows
- merges inconsistent spellings of college and institution names
- standardizes dates and tier labels
- flags missing values instead of inventing them
- writes a `data_quality_report.txt` showing exactly what was changed and how many rows were affected

## Tech stack

Python, Streamlit, pandas, Plotly

## Running it

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Add your own data in this layout (the original files are not included):

   ```
   data/
   ├── raw/      # your .xlsx trackers (used by clean_data.py)
   └── clean/    # activations_clean.csv, fest_tracker_clean.csv, events_3p_clean.csv
   ```

   The CSVs in `data/clean/` need these columns:

   - `activations_clean.csv`: `college_name`, `owner_sm_name`, `activation_date`, `assets_required`, `asset_qty`, `budget`, ...
   - `fest_tracker_clean.csv`: `institution_name`, `fest_name`, `tier`, `crowd_approx`, `lost_to_competition_flag`, ...
   - `events_3p_clean.csv`: `event_name`, `total_cost`, `cans_sold`, `people_present`, ...

3. Run the cleaner (only needed if you start from raw Excel files), then launch the app:

   ```bash
   python3 clean_data.py
   streamlit run app.py
   ```

   The app opens at `http://localhost:8501`.

## Project structure

```
app.py                  # Streamlit dashboard (5 pages)
clean_data.py           # Excel -> clean CSV pipeline + data quality report
requirements.txt
.streamlit/config.toml  # dark theme
static/                 # fonts (Inter, JetBrains Mono; open font licences included)
```

## Author

Shrey Anchal | [LinkedIn](https://www.linkedin.com/in/shrey-anchal) | [GitHub](https://github.com/Shrey-05)
