"""
db_helpers.py
--------------
Low-level utilities that talk to the SQLite database directly.
No LLM logic lives here — just schema reading, query execution,
and cleaning raw LLM text into runnable SQL.
"""

import re
import sqlite3
import pandas as pd


def get_schema(db_path: str) -> str:
    """
    Auto-detect the schema of ANY SQLite database file.

    Instead of hand-writing the schema as a string, this connects to the
    .db file, reads sqlite_master for the table list, then PRAGMA
    table_info(table) for each table's columns + types, and formats it
    into the same style of text block the prompts expect:

        Table name: transactions
        id (INTEGER)
        product_id (INTEGER)
        ...

    Works for single-table or multi-table databases.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        # Get all user tables (skip SQLite's internal tables)
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            raise ValueError(f"No tables found in database: {db_path}")

        schema_blocks = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            # columns row shape: (cid, name, type, notnull, dflt_value, pk)
            col_lines = [f"{col[1]} ({col[2]})" for col in columns]
            block = f"Table name: {table}\n" + "\n".join(col_lines)
            schema_blocks.append(block)

        return "\n\n".join(schema_blocks)
    finally:
        conn.close()


def list_tables(db_path: str) -> list[str]:
    """Return just the table names in the database (used for quick previews)."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def clean_sql(raw_text: str) -> str:
    """
    Strip markdown code fences, language tags, and stray formatting that
    LLMs often wrap around SQL, e.g.:

        ```sql
        SELECT * FROM transactions;
        ```

    Returns plain, directly-runnable SQL text.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # Remove ```sql ... ``` or ``` ... ``` fences
    fence_match = re.search(r"```(?:sql)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        text = fence_match.group(1).strip()

    # Remove any leftover stray backticks or a leading "sql" word
    text = text.strip("`").strip()
    if text.lower().startswith("sql\n"):
        text = text[4:].strip()
    elif text.lower().startswith("sql "):
        text = text[4:].strip()

    return text.strip()


def execute_sql(sql_query: str, db_path: str) -> pd.DataFrame:
    """
    Run a (already-cleaned) SQL query against the given SQLite database
    and return the result as a pandas DataFrame.
    """
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql_query, conn)
    finally:
        conn.close()
    return df
