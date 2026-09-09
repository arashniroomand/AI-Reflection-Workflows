"""
sql_pipeline.py
----------------
All LLM-facing logic lives here: generating SQL, and the two reflection
strategies (query-level review, and result-grounded review).

No Streamlit code and no raw prompt-writing happens outside this file —
app.py only imports and calls these functions.
"""

import json
import pandas as pd
import aisuite as ai
from dotenv import load_dotenv

from utils.db_helpers import clean_sql

load_dotenv()
client = ai.Client()

DEFAULT_MODEL = "openai:gemini-2.5-flash-lite"
REFLECTION_MODEL = "openai:gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# V1 — Direct generation
# ---------------------------------------------------------------------------
def generate_sql(question: str, schema: str, model: str = DEFAULT_MODEL) -> str:
    """
    Generate a SQL query directly from the user's question and the schema.
    No reflection involved — this is the baseline (V1).
    """
    prompt = f"""
You are a SQL assistant. Given the schema and the user's question, write a SQL query for SQLite.

Schema:
{schema}

User question:
{question}

Respond with the SQL only.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    return clean_sql(raw)


# ---------------------------------------------------------------------------
# V2 — Self-review at the QUERY level (doesn't see the result, only the SQL)
# ---------------------------------------------------------------------------
def refine_sql(
    question: str,
    sql_query: str,
    schema: str,
    model: str = REFLECTION_MODEL,
) -> tuple[str, str]:
    """
    Reflect on whether the SQL query *itself* (not its output) looks like
    it correctly answers the question, and propose an improved SQL if needed.
    Returns (feedback, refined_sql).
    """
    prompt = f"""
You are a SQL reviewer and refiner.

User asked:
{question}

Original SQL:
{sql_query}

Table Schema:
{schema}

Step 1: Briefly evaluate if this SQL query is likely to fully answer the user's question.
Step 2: If improvement is needed, provide a refined SQL query for SQLite.
If the original SQL is already correct, return it unchanged.

Return STRICT JSON with two fields:
{{
  "feedback": "<1-3 sentences explaining the gap or confirming correctness>",
  "refined_sql": "<final SQL to run>"
}}
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return _parse_feedback_response(response.choices[0].message.content, fallback_sql=sql_query)


# ---------------------------------------------------------------------------
# V3 — Result-grounded reflection (sees the actual output table)
# ---------------------------------------------------------------------------
def refine_sql_external_feedback(
    question: str,
    sql_query: str,
    df_feedback: pd.DataFrame,
    schema: str,
    model: str = REFLECTION_MODEL,
) -> tuple[str, str]:
    """
    Evaluate whether the SQL result actually answers the user's question,
    and if not, propose a refined query. This version sees the real output
    table, not just the query text.
    Returns (feedback, refined_sql).
    """
    prompt = f"""
You are a SQL reviewer and refiner.

User asked:
{question}

Original SQL:
{sql_query}

SQL Output:
{df_feedback.to_markdown(index=False)}

Table Schema:
{schema}

Step 1: Briefly evaluate if the SQL output answers the user's question.
Step 2: If the SQL could be improved, provide a refined SQL query.
If the original SQL is already correct, return it unchanged.

Return a strict JSON object with two fields:
- "feedback": brief evaluation and suggestions
- "refined_sql": the final SQL to run
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )

    return _parse_feedback_response(response.choices[0].message.content, fallback_sql=sql_query)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------
def _parse_feedback_response(content: str, fallback_sql: str) -> tuple[str, str]:
    """
    Parse the {"feedback": ..., "refined_sql": ...} JSON both reflection
    functions expect back from the LLM, cleaning the SQL and falling back
    gracefully if the model didn't return valid JSON.
    """
    try:
        obj = json.loads(content)
        feedback = str(obj.get("feedback", "")).strip()
        refined_sql = clean_sql(str(obj.get("refined_sql", fallback_sql)))
        if not refined_sql:
            refined_sql = fallback_sql
    except Exception:
        feedback = content.strip()
        refined_sql = fallback_sql

    return feedback, refined_sql