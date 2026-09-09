# SQL Reflection Demo

A Streamlit app that shows the effect of reflection on LLM-generated SQL,
in three versions:

- **V1 — Direct Generation**: LLM writes SQL from the question only.
- **V2 — Self-Review (query-level)**: A second LLM call looks at the *query itself*
  and rewrites it if it looks wrong, before running it.
- **V3 — Result-Grounded Reflection**: A second LLM call looks at the *actual result
  table* from V1 and gives feedback + a corrected query if needed.

Works with **any SQLite database** — the schema is auto-detected from the file,
nothing is hardcoded.

## Project structure

```
sql_reflection_app/
├── app.py                  # Streamlit UI only
├── sql_pipeline.py         # generate_sql, refine_sql, refine_sql_external_feedback
├── utils/
│   └── db_helpers.py       # get_schema (auto-detect), execute_sql, clean_sql
├── data/
│   └── products.db         # put your default database here
├── requirements.txt
└── .env                    # your API keys (see below)
```

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with whatever keys `aisuite`
   needs for the providers you're using, e.g.:
   ```
   OPENAI_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

3. Put a SQLite database at `data/products.db`, **or** just run the app and
   upload any `.db` file from the "Database source" panel — the schema is
   detected automatically either way.

## Run

```
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## How the schema auto-detection works

`utils/db_helpers.get_schema(db_path)` connects to the SQLite file, reads
`sqlite_master` for the table list, then runs `PRAGMA table_info(table)` for
each table to get column names + types. It formats this into the same
`Table name: ... / col (TYPE)` text block the prompts use — so it's a drop-in
replacement for the hardcoded schema string, and it works for single-table or
multi-table databases.

## Notes

- `clean_sql()` strips ` ```sql ` fences and stray backticks from LLM output
  before anything is executed — protects against the query failing purely due
  to markdown formatting.
- Model names (`openai:gpt-4.1` for generation, `openai:gemini-2.5-flash-lite`
  for reflection) are set as constants at the top of `sql_pipeline.py` — change
  them there if you want to try different models per version.
