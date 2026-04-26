def generate_insights(df):
    insights = []

    # Basic shape
    rows, cols = df.shape
    insights.append(f"Dataset has {rows} rows and {cols} columns.")

    # Missing values
    total_missing = df.isnull().sum().sum()
    insights.append(f"Total missing values: {total_missing}")

    # Numeric analysis
    numeric_cols = df.select_dtypes(include=["number"]).columns

    if len(numeric_cols) > 0:
        max_col = df[numeric_cols].mean().idxmax()
        min_col = df[numeric_cols].mean().idxmin()

        insights.append(f"'{max_col}' has the highest average value.")
        insights.append(f"'{min_col}' has the lowest average value.")

    # Categorical analysis
    categorical_cols = df.select_dtypes(include=["object"]).columns

    if len(categorical_cols) > 0:
        col = categorical_cols[0]
        top_value = df[col].value_counts().idxmax()
        insights.append(f"Most frequent value in '{col}' is '{top_value}'.")

    return insights


def dataset_intelligence(df):
    return {
        "numeric": df.select_dtypes(include=["number"]).columns.tolist(),
        "categorical": df.select_dtypes(include=["object"]).columns.tolist(),
        "datetime": df.select_dtypes(include=["datetime64"]).columns.tolist()
    }


def detect_time_column(df):
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            return col
    return None


def detect_numeric_columns(df):
    return df.select_dtypes(include=["number"]).columns.tolist()