import io
import pandas as pd


def load_data(file_source) -> pd.DataFrame:
    """Load a DataFrame from a file path or uploaded buffer."""
    if isinstance(file_source, str):
        return pd.read_csv(file_source)
    return pd.read_csv(io.BytesIO(file_source.getvalue()))


def extract_schema_info(df: pd.DataFrame) -> str:
    """Dynamically extract column names, data types, and preview rows for the LLM prompt."""
    col_types = df.dtypes.to_string()
    sample_rows = df.head(2).to_string(index=False)
    
    schema_str = (
        "DataFrame Schema (variable name is 'df'):\n"
        f"Columns and Data Types:\n{col_types}\n\n"
        f"First 2 rows sample:\n{sample_rows}"
    )
    return schema_str