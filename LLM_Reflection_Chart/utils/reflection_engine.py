import re
import json
import pandas as pd
from utils.data_helpers import extract_schema_info
from utils.llm_helpers import get_response, image_openai_call  # <--- Changed here


def execute_generated_code(code_str: str, df: pd.DataFrame) -> tuple[bool, str]:
    """Safely execute generated Python code in an isolated scope."""
    # FIX: Use a single dictionary for BOTH globals and locals. 
    # This prevents the Python 3 scope bug with list comprehensions inside exec().
    sandbox_scope = {
        "__builtins__": __builtins__,
        "df": df.copy()
    }
    
    try:
        # Pass sandbox_scope as BOTH the globals and locals arguments
        exec(code_str, sandbox_scope, sandbox_scope)
        return True, "Execution successful"
    except Exception as e:
        return False, str(e)


def extract_code_block(llm_output: str) -> str:
    """Extract code from <execute_python> tags using regex."""
    match = re.search(r"<execute_python>([\s\S]*?)</execute_python>", llm_output)
    if match:
        return match.group(1).strip()
    
    code_match = re.search(r"```python([\s\S]*?)```", llm_output)
    if code_match:
        return code_match.group(1).strip()
        
    return llm_output.strip()


def generate_initial_chart(instruction: str, model_name: str, out_path: str, df: pd.DataFrame) -> str:
    """Generate initial Python visualization code from prompt and schema."""
    schema_info = extract_schema_info(df)
    
    prompt = f"""
    You are a data visualization expert.

    Return your answer *strictly* in this format:

    <execute_python>
    # valid python code here
    </execute_python>

    Do not add explanations, only the tags and the code.

    {schema_info}

    User instruction: {instruction}

    Requirements for the code:
    1. Assume the DataFrame is already loaded as 'df'.
    2. Use matplotlib for plotting.
    3. Add clear title, axis labels, and legend if needed.
    4. Save the figure as '{out_path}' with dpi=300.
    5. Do not call plt.show().
    6. Close all plots with plt.close().
    7. Add all necessary python import statements.

    Return ONLY the code wrapped in <execute_python> tags.
    """
    
    response = get_response(model_name, prompt)
    return extract_code_block(response)


def reflect_on_image_and_regenerate(
    chart_path: str,
    instruction: str,
    model_name: str,
    out_path_v2: str,
    code_v1: str,
    df: pd.DataFrame
) -> tuple[str, str]:
    """Critique the generated chart image and original code, then return refined code."""
    schema_info = extract_schema_info(df)
    
    prompt = f"""
    You are a data visualization expert.
    Your task: critique the attached chart and the original code against the given instruction,
    then return improved matplotlib code.

    Original code (for context):
    {code_v1}

    OUTPUT FORMAT (STRICT):
    1) Provide a valid JSON object containing ONLY the "feedback" field.
    Example: {{"feedback": "The legend overlaps with title and axis labels are cramped."}}

    2) Output the refined Python code wrapped in:
    <execute_python>
    ...
    </execute_python>

    3) Import all necessary libraries in the code.

    HARD CONSTRAINTS:
    - Do NOT include extra markdown outside the specified structures.
    - Use pandas/matplotlib only.
    - Assume 'df' already exists; do not read files.
    - Save to '{out_path_v2}' with dpi=300.
    - Always call plt.close() at the end (no plt.show()).

    {schema_info}

    Instruction:
    {instruction}
    """

    content = image_openai_call(model_name, prompt, chart_path) # <--- Changed here

    feedback_text = "No critique generated."
    json_match = re.search(r"\{[\s\S]*?\"feedback\"[\s\S]*?\}", content)
    if json_match:
        try:
            parsed_json = json.loads(json_match.group(0))
            feedback_text = parsed_json.get("feedback", feedback_text)
        except Exception:
            feedback_text = "Failed to parse structured feedback JSON."

    refined_code = extract_code_block(content)
    return feedback_text, refined_code