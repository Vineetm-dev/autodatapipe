from openai import OpenAI
import pandas as pd

client = OpenAI()

# ============================= #
# AUTO INSIGHTS
# ============================= #

def generate_ai_insights(df):
    try:
        sample = df.head(20).to_csv(index=False)

        prompt = f"""
You are a senior data analyst.

Analyze this dataset and provide:
1. What the dataset represents
2. Key trends
3. Interesting insights

Dataset:
{sample}
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception:
        return "⚠️ AI insights unavailable (using basic logic)."


# ============================= #
# CHAT WITH DATA
# ============================= #

def ask_ai_about_data(df, question, chat_history=None):
    try:
        df = df.copy()

        # ----------------------------
        # 🧠 COLUMN INTELLIGENCE
        # ----------------------------
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        # Detect possible target column
        target_col = None
        for col in df.columns:
            if col.lower() in ["target", "label", "outcome", "survived", "status"]:
                target_col = col

        # ----------------------------
        # 🧠 CONTEXT BUILDING
        # ----------------------------
        column_info = f"""
Columns:
- Numeric: {numeric_cols}
- Categorical: {categorical_cols}
- Datetime: {datetime_cols}
- Target (if any): {target_col}
"""

        sample = df.head(15).to_csv(index=False)

        history_text = ""
        if chat_history:
            last_msgs = chat_history[-6:]
            history_text = "\n".join([f"{s}: {m}" for s, m in last_msgs])

        # ----------------------------
        # 🧠 SMART PROMPT
        # ----------------------------
        prompt = f"""
You are an expert data analyst.

Understand the dataset structure and answer precisely.

{column_info}

Dataset sample:
{sample}

Conversation:
{history_text}

User question:
{question}

Rules:
- Use column names correctly
- If counting, calculate properly
- If unsure, infer from column types
- Be concise and accurate
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception:
        return basic_fallback_answer(df, question)

# ============================= #
# SMART FALLBACK (WORKS WITHOUT AI)
# ============================= #

def basic_fallback_answer(df, question):
    df = df.copy()
    question = question.lower()

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Convert all numeric safely
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()

    # Try detect target column
    target_col = None
    for col in df.columns:
        if col.lower() in ["survived", "target", "label", "outcome", "result"]:
            target_col = col
            df[target_col] = pd.to_numeric(df[target_col], errors="coerce")
    
    # 🔍 detect column from question (SMART LAYER)
    for col in df.columns:
        if col.lower() in question.replace("_", " "):
            if col in numeric_cols:
                return f"{col} average is {round(df[col].mean(), 2)}"
            if col in categorical_cols:
                top = df[col].value_counts().idxmax()
                return f"Most common value in {col} is {top}"

    # -----------------------------
    # COUNT / SIZE
    # -----------------------------
    if any(k in question for k in ["how many", "count", "total", "rows"]):
        return f"The dataset has {df.shape[0]} rows."

    # -----------------------------
    # MEAN / AVERAGE
    # -----------------------------
    if any(k in question for k in ["average", "mean"]):
        if numeric_cols:
            col = numeric_cols[0]
            return f"Average {col} is {round(df[col].mean(), 2)}."

    # -----------------------------
    # MAX / MIN
    # -----------------------------
    if "max" in question:
        if numeric_cols:
            col = numeric_cols[0]
            return f"Maximum {col} is {df[col].max()}."

    if "min" in question:
        if numeric_cols:
            col = numeric_cols[0]
            return f"Minimum {col} is {df[col].min()}."

    # -----------------------------
    # GROUP BY
    # -----------------------------
    if any(k in question for k in ["by", "per", "group"]):
        if categorical_cols and numeric_cols:
            cat = categorical_cols[0]
            num = numeric_cols[0]
            grouped = df.groupby(cat)[num].mean()
            return f"Average {num} by {cat}:\n{grouped.to_string()}"

    # -----------------------------
    # TARGET ANALYSIS (GENERIC)
    # -----------------------------
    if target_col:
        if any(k in question for k in ["died", "death", "failed", "not survived"]):
            count = df[df[target_col] == 0].shape[0]
            return f"{count} entries have {target_col} = 0."

        if any(k in question for k in ["survived", "success", "passed"]):
            count = df[df[target_col] == 1].shape[0]
            return f"{count} entries have {target_col} = 1."

    # -----------------------------
    # DEFAULT
    # -----------------------------
    return "AI is unavailable, but I can answer basic questions like count, average, max/min, and trends."


# ============================= #
# CHART EXPLANATION
# ============================= #

def explain_chart(df, chart_type, x_col, y_col=None):
    try:
        df = df.copy()

        preview_cols = [x_col] + ([y_col] if y_col else [])
        preview = df[preview_cols].head(10).to_csv(index=False)

        prompt = f"""
Explain this chart in simple terms.

Chart type: {chart_type}
X column: {x_col}
Y column: {y_col}

Data sample:
{preview}
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception:
        return fallback_chart_explanation(df, chart_type, x_col, y_col)


def fallback_chart_explanation(df, chart_type, x_col, y_col=None):

    if chart_type == "histogram":
        return f"This shows how {x_col} values are distributed."

    if chart_type == "bar" and y_col:
        grouped = df.groupby(x_col)[y_col].mean()
        top = grouped.idxmax()
        return f"{top} has the highest average {y_col}."

    if chart_type == "line" and y_col:
        return f"This shows how {y_col} changes over {x_col}."

    if chart_type == "scatter" and y_col:
        return f"This shows relationship between {x_col} and {y_col}."

    return "Basic chart explanation available."