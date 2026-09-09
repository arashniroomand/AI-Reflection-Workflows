"""
app.py
------
Streamlit UI only. All LLM logic lives in sql_pipeline.py,
all database logic lives in utils/db_helpers.py.

Run with:  streamlit run app.py
"""

import os
import streamlit as st

from utils.db_helpers import get_schema, execute_sql
from sql_pipeline import generate_sql, refine_sql, refine_sql_external_feedback

DEFAULT_DB_PATH = "data/products.db"
SUGGESTED_QUESTION = "Which color of product has the highest total sales?"

# ---------------------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------------------
st.set_page_config(page_title="SQL Reflection Demo", page_icon="🗄️", layout="centered")

# Dark background with high-contrast text, and a distinct accent color
# per version so V1 / V2 / V3 are visually easy to tell apart.
ACCENT_V1 = "#4C8BF5"  # blue
ACCENT_V2 = "#F5A623"  # amber
ACCENT_V3 = "#3DBE72"  # green
CARD_BG = "#1B1F27"
TEXT_COLOR = "#FAFAFA"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: #0E1117;
        color: {TEXT_COLOR};
    }}
    .version-card {{
        background-color: {CARD_BG};
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.5rem;
        color: {TEXT_COLOR};
    }}
    .version-title {{
        font-weight: 700;
        font-size: 1.05rem;
        margin-bottom: 0.6rem;
    }}
    .feedback-box {{
        background-color: #262B36;
        border-radius: 6px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.8rem;
        color: {TEXT_COLOR};
        font-size: 0.92rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "question" not in st.session_state:
    st.session_state.question = ""
if "db_path" not in st.session_state:
    st.session_state.db_path = DEFAULT_DB_PATH


def use_suggested_question():
    st.session_state.question = SUGGESTED_QUESTION


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>🗄️ SQL Reflection Demo</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#B0B7C3;'>"
    "Compare direct generation vs. self-review vs. result-grounded reflection."
    "</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Database selection — works with ANY SQLite database, not just products.db
# ---------------------------------------------------------------------------
with st.expander("📂 Database source", expanded=False):
    uploaded_db = st.file_uploader("Upload a .db / .sqlite file", type=["db", "sqlite", "sqlite3"])
    if uploaded_db is not None:
        os.makedirs("data/uploaded", exist_ok=True)
        save_path = os.path.join("data/uploaded", uploaded_db.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_db.getbuffer())
        st.session_state.db_path = save_path
        st.success(f"Using uploaded database: {uploaded_db.name}")
    else:
        st.caption(f"Currently using default: `{st.session_state.db_path}`")

db_path = st.session_state.db_path

if not os.path.exists(db_path):
    st.error(f"Database not found at `{db_path}`. Upload a .db file above to continue.")
    st.stop()

# Auto-detect schema for whatever database is currently selected
schema = get_schema(db_path)

with st.expander("🔍 Detected schema"):
    st.code(schema, language="text")

# ---------------------------------------------------------------------------
# Centered "chat" input box
# ---------------------------------------------------------------------------
st.button(f"💡 Try: \"{SUGGESTED_QUESTION}\"", on_click=use_suggested_question)

question = st.text_input(
    "Ask a question about your data",
    key="question",
    placeholder="e.g. Which color of product has the highest total sales?",
)

run_clicked = st.button("Run ▶", use_container_width=True)


# ---------------------------------------------------------------------------
# Rendering helper for a single version block
# ---------------------------------------------------------------------------
def render_version(title: str, accent: str, feedback: str | None, sql: str, df):
    st.markdown(
        f"<div class='version-card' style='border-left: 5px solid {accent};'>"
        f"<div class='version-title' style='color:{accent};'>{title}</div>",
        unsafe_allow_html=True,
    )
    if feedback:
        st.markdown(f"<div class='feedback-box'><b>Feedback:</b> {feedback}</div>", unsafe_allow_html=True)
    st.code(sql, language="sql")
    if df is not None:
        if df.empty:
            st.caption("Query ran successfully but returned no rows.")
        else:
            st.dataframe(df, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main flow: generate V1 -> V2 -> V3
# ---------------------------------------------------------------------------
if run_clicked:
    if not question.strip():
        st.warning("Please enter a question first.")
        st.stop()

    # Defaults so every variable exists even if a step below fails partway
    sql_v1, df_v1, v1_error = "", None, None
    sql_v2, df_v2, feedback_v2, v2_error = "", None, None, None
    sql_v3, df_v3, feedback_v3, v3_error = "", None, None, None

    with st.spinner("Generating and reflecting..."):
        # --- V1: direct generation ---
        try:
            sql_v1 = generate_sql(question, schema)
            df_v1 = execute_sql(sql_v1, db_path)
        except Exception as e:
            v1_error = str(e)

        # --- V2: query-level self-review (only if V1 produced a query) ---
        if sql_v1:
            try:
                feedback_v2, sql_v2 = refine_sql(question, sql_v1, schema)
                df_v2 = execute_sql(sql_v2, db_path)
            except Exception as e:
                sql_v2 = sql_v2 or sql_v1
                v2_error = str(e)
        else:
            v2_error = "Skipped — V1 did not produce a query."

        # --- V3: result-grounded reflection (only if V1 produced a query) ---
        if sql_v1:
            try:
                source_df = df_v1 if df_v1 is not None else df_v2
                feedback_v3, sql_v3 = refine_sql_external_feedback(question, sql_v1, source_df, schema)
                df_v3 = execute_sql(sql_v3, db_path)
            except Exception as e:
                sql_v3 = sql_v3 or sql_v1
                v3_error = str(e)
        else:
            v3_error = "Skipped — V1 did not produce a query."

    st.divider()

    render_version("V1 — Direct Generation", ACCENT_V1, None, sql_v1, df_v1)
    if v1_error:
        st.error(f"V1 execution error: {v1_error}")

    render_version("V2 — Self-Review (query-level)", ACCENT_V2, feedback_v2, sql_v2, df_v2)
    if v2_error:
        st.error(f"V2 execution error: {v2_error}")

    render_version("V3 — Result-Grounded Reflection", ACCENT_V3, feedback_v3, sql_v3, df_v3)
    if v3_error:
        st.error(f"V3 execution error: {v3_error}")