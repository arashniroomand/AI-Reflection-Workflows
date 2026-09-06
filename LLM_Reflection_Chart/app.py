import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv  # <--- 1. Import load_dotenv

# 2. Load environment variables from .env file
load_dotenv()


from utils.data_helpers import load_data
from utils.reflection_engine import (
    generate_initial_chart,
    reflect_on_image_and_regenerate,
    execute_generated_code,
)

st.set_page_config(
    page_title="LLM Self-Reflection System",
    page_icon="📊",
    layout="wide"
)

# 1. FIX: Added color: #000000; to the CSS so the text is readable in dark mode
st.markdown("""
    <style>
    .feedback-card {
        background-color: #f0f2f6;
        color: #000000; 
        padding: 16px;
        border-radius: 8px;
        border-left: 5px solid #0066cc;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


st.title("📊 LLM Visual Self-Reflection Engine")
st.caption("Demonstrating multi-modal feedback loops for automated data visualization refinement.")

if "df" not in st.session_state:
    st.session_state.df = None
if "code_v1" not in st.session_state:
    st.session_state.code_v1 = None
if "code_v2" not in st.session_state:
    st.session_state.code_v2 = None
if "feedback" not in st.session_state:
    st.session_state.feedback = None

# Sidebar Configuration for OpenAI/GapGPT Endpoint
with st.sidebar:
    st.header("API & Model Config")
    
    selected_model = st.text_input(
        "Model Name",
        value="gemini-2.5-flash-lite"
    )
    
    base_url = st.text_input(
        "Base URL",
        value="https://api.gapgpt.app/v1"
    )
    os.environ["OPENAI_BASE_URL"] = base_url
    
    api_key = st.text_input("API Key", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    # 3. NEW: Sidebar section explaining the Reflexion paper + image.png
    st.divider()
    st.header("Research Foundation")
    st.markdown("""
    **Reflexion: Language Agents with Verbal Reinforcement Learning**  
    *(Noah Shinn et al., 2023)*
    
    Unlike traditional reinforcement learning that requires expensive model weight updates, **Reflexion** reinforces agents using *linguistic feedback*. 
    
    The framework allows an LLM agent to evaluate its own output, generate natural language reflections on its mistakes, and store these insights in an episodic memory buffer. In subsequent attempts, the agent reads its own reflections to avoid repeating errors, significantly improving outcomes in reasoning and coding tasks.
    """)
    
    # Add the second requested image under the explanation
    try:
        st.image("img/image.png", use_container_width=True)
    except Exception:
        st.warning("Please ensure img/image.png exists.")
# Section 1: Data Management
st.subheader("1. Dataset Selection")
uploaded_file = st.file_uploader("Upload custom CSV file", type=["csv"])

default_data_path = "data/coffee_sales.csv"

if uploaded_file is not None:
    st.session_state.df = load_data(uploaded_file)
    st.success("Uploaded CSV loaded successfully.")
elif os.path.exists(default_data_path):
    st.session_state.df = load_data(default_data_path)
    st.info("Loaded default dataset: coffee_sales.csv")

if st.session_state.df is not None:
    with st.expander("Preview Dataset Schema & Sample Rows"):
        st.dataframe(st.session_state.df.sample(min(5, len(st.session_state.df))))

st.divider()

# Section 2: Prompt and Execution
st.subheader("2. Visualization Instruction")
user_instruction = st.text_area(
    "Enter visualization instruction:",
    value="Create a plot comparing Q1 coffee sales in 2024 and 2025 using the data.",
    height=100
)

col_gen, col_reflect = st.columns([1, 1])

with col_gen:
    if st.button("Generate Initial Chart (V1)", type="primary"):
        if not os.environ.get("OPENAI_API_KEY"):
            st.error("Please provide an API Key in the sidebar.")
        elif st.session_state.df is None:
            st.error("No dataset available.")
        else:
            with st.spinner("Generating initial chart code..."):
                code_v1 = generate_initial_chart(
                    instruction=user_instruction,
                    model_name=selected_model,
                    out_path="chart_v1.png",
                    df=st.session_state.df
                )
                st.session_state.code_v1 = code_v1
                
                success, msg = execute_generated_code(code_v1, st.session_state.df)
                if not success:
                    st.error(f"Execution Error: {msg}")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Draft 1 (Initial Generation)")
    if st.session_state.code_v1:
        st.code(st.session_state.code_v1, language="python")
        if os.path.exists("chart_v1.png"):
            st.image("chart_v1.png", caption="Chart V1 Output", use_container_width=True)

with col_reflect:
    if st.session_state.code_v1 and os.path.exists("chart_v1.png"):
        if st.button("Run Self-Reflection Loop 🔁"):
            with st.spinner("Analyzing image and refining code..."):
                feedback, code_v2 = reflect_on_image_and_regenerate(
                    chart_path="chart_v1.png",
                    instruction=user_instruction,
                    model_name=selected_model,
                    out_path_v2="chart_v2.png",
                    code_v1=st.session_state.code_v1,
                    df=st.session_state.df
                )
                st.session_state.feedback = feedback
                st.session_state.code_v2 = code_v2
                
                success, msg = execute_generated_code(code_v2, st.session_state.df)
                if not success:
                    st.error(f"Refined Code Execution Error: {msg}")

with col2:
    st.markdown("### Draft 2 (Self-Reflected Version)")
    if st.session_state.feedback:
        st.markdown(
            f'<div class="feedback-card"><b>LLM Visual Critique:</b><br>{st.session_state.feedback}</div>',
            unsafe_allow_html=True
        )
    if st.session_state.code_v2:
        st.code(st.session_state.code_v2, language="python")
        if os.path.exists("chart_v2.png"):
            st.image("chart_v2.png", caption="Chart V2 Output (Refined)", use_container_width=True)