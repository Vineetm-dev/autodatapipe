# ============================= #
# IMPORTS
# ============================= #

import streamlit as st
import pandas as pd
import requests
import logging
from backend.auth import create_users_table, signup_user, login_user
from dotenv import load_dotenv

from backend.etl_module import run_etl
from backend.db import save_to_db, load_user_datasets
from backend.analytics import generate_insights
from backend.charts import (
    recommended_charts,
    histogram_chart,
    bar_chart,
    scatter_chart,
    line_chart
)
from backend.ai import generate_ai_insights, ask_ai_about_data, explain_chart

# ============================= #
# CONFIG
# ============================= #

load_dotenv()
logging.basicConfig(level=logging.INFO)

if "df" not in st.session_state:
    st.session_state.df = None

# ============================= #
# AUTH STATE INIT
# ============================= #

create_users_table()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = None    

# ============================= #
# HELPER FUNCTION
# ============================= #

def fetch_api_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame([{
                "asset": "bitcoin",
                "usd_price": data["bitcoin"]["usd"],
                "timestamp": pd.Timestamp.now()
            }])
        return None

    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# ============================= #
# UI
# ============================= #

st.set_page_config(layout="wide", page_title="AutoDataPipe", page_icon="📊")

st.title("AutoDataPipe: Your AI Dashboard 📊🤖")
st.markdown("Turn any CSV dataset into insights instantly 🚀")
st.markdown("---")

# ============================= #
# AUTH UI
# ============================= #

if not st.session_state.authenticated:

    st.title("🔐 Login to AutoDataPipe")

    auth_mode = st.radio("Choose", ["Login", "Signup"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_mode == "Signup":
        if st.button("Create Account"):
            if username and password:
                res = signup_user(username, password)

                if res == "success":
                    st.success("Account created! Now login.")
                else:
                    st.error("Username already exists")
            else:
                st.warning("Enter username and password")

    else:  # Login
        if st.button("Login"):
            if login_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Logged in!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# ============================= #
# SIDEBAR
# ============================= #

with st.sidebar:

    # =========================
    # BRANDING
    # =========================
    st.markdown("## 🚀 AutoDataPipe")
    st.caption("AI-powered data insights")

    st.markdown("---")

    # =========================
    # USER SECTION
    # =========================
    st.markdown("### 👤 Account")

    st.success(f"Logged in as\n**{st.session_state.username}**")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

    with col2:
        if st.button("🧹 Clear"):
            st.session_state.df = None
            st.success("Session cleared")
            st.rerun()

    st.markdown("---")

    # =========================
    # DATA MANAGEMENT
    # =========================
    st.markdown("### 📂 Your Data")

    if st.button("📥 Load My Data"):
        user_df = load_user_datasets(st.session_state.username)

        if user_df is not None and not user_df.empty:
            st.session_state.df = user_df
            st.success("Loaded latest dataset")
            st.rerun()
        else:
            st.warning("No datasets found")

    # Preview dataset
    if st.session_state.get("df") is not None:
        with st.expander("👀 Preview Data"):
            st.dataframe(st.session_state.df.head(5))

    st.markdown("---")

    # =========================
    # DATA STATUS
    # =========================
    st.markdown("### 📊 Data Status")

    if st.session_state.get("df") is not None:
        df = st.session_state.df

        st.metric("Rows", df.shape[0])
        st.metric("Columns", df.shape[1])

        missing = int(df.isnull().sum().sum())
        st.metric("Missing", missing)

    else:
        st.info("No data loaded")

    st.markdown("---")

    # =========================
    # FEATURES PANEL
    # =========================
    st.markdown("### ⚙️ Features")

    st.write("✔ Upload CSV")
    st.write("✔ API Fetch")
    st.write("✔ AI Insights")
    st.write("✔ Chat with Data")
    st.write("✔ Smart Charts")

    st.markdown("---")

    # =========================
    # APP STATUS
    # =========================
    st.markdown("### 🧠 System")

    st.success("App running")

# ============================= #
# DATA INPUT
# ============================= #

data_source = st.radio("Select Data Source", ["Upload CSV", "Fetch API Data"])

if data_source == "Upload CSV":
    file = st.file_uploader("Upload CSV", type=["csv"])

    if file:
        df = run_etl(file=file)
        st.session_state.df = df
        st.success("CSV uploaded!")

elif data_source == "Fetch API Data":
    if st.button("Fetch API"):
        df = fetch_api_data()
        if df is not None:
            df = run_etl(api_data=df, source="API")
            st.session_state.df = df
            st.success("API loaded!")
        else:
            st.error("API failed")

# ============================= #
# LOAD DATA
# ============================= #

df = st.session_state.get("df")

if df is None:
    st.info("Upload data to continue")
    st.stop()

df = df.copy()

# ============================= #
# BASIC CLEANING
# ============================= #

df = df.copy()

# Convert problematic pandas dtypes to safe ones
for col in df.columns:
    # Fix nullable integers
    if str(df[col].dtype) == "Int64":
        df[col] = df[col].astype("float64")

    # Fix mixed/object columns
    elif df[col].dtype == "object":
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            df[col] = df[col].astype(str)

# Final safety conversion
df = df.convert_dtypes()
# ============================= #
# DOWNLOAD + DB
# ============================= #

st.download_button("Download CSV", df.to_csv(index=False), "clean.csv")

col1, col2 = st.columns(2)

with col1:
    if st.button("Save to DB"):
        save_to_db(df, st.session_state.username)
        st.success("Saved")

with col2:
    if st.button("Load from DB"):
        st.write(load_from_db().head())

# ============================= #
# METRICS
# ============================= #

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows", df.shape[0])
c2.metric("Columns", df.shape[1])
c3.metric("Missing", int(df.isnull().sum().sum()))
c4.metric("Duplicates", int(df.duplicated().sum()))

# ============================= #
# DASHBOARD
# ============================= #

st.subheader("📊 Dashboard")

num_cols = df.select_dtypes(include=["number"]).columns.tolist()
cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

metric = st.selectbox("Metric", num_cols) if num_cols else None
category = st.selectbox("Category", cat_cols) if cat_cols else None

col1, col2 = st.columns(2)

if metric:
    with col1:
        fig = histogram_chart(df, metric)
        st.plotly_chart(fig, width="stretch")

        if st.button(f"Explain {metric}", key="hist_explain"):
            explanation = explain_chart(df, "histogram", metric)
            st.info(explanation)

    with col2:
        fig = bar_chart(df, category, metric)
        st.plotly_chart(fig, width="stretch")

        if st.button(f"Explain {category} vs {metric}", key="bar_explain"):
            explanation = explain_chart(df, "bar", category, metric)
            st.info(explanation)
# ============================= #
# TIME SERIES
# ============================= #

time_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
time_col = time_cols[0] if time_cols else None
if time_cols and metric:
    st.subheader("📈 Time Trend")
    fig = line_chart(df, time_col, metric)
    st.plotly_chart(fig, width="stretch")

    if st.button("Explain trend", key="line_explain"):
        explanation = explain_chart(df, "line", time_col, metric)
        st.info(explanation)

# ============================= #
# RECOMMENDED CHARTS
# ============================= #

st.subheader("🎨 Recommended Charts")

for i, (chart_type, cols) in enumerate(recommended_charts(df)):

    if chart_type == "Histogram for numeric columns":
        st.plotly_chart(histogram_chart(df, cols), key=f"h{i}")

    elif chart_type == "Scatter plot for numeric columns":
        x, y = cols
        st.plotly_chart(scatter_chart(df, x, y), key=f"s{i}")

    elif chart_type == "Bar chart for category vs metric":
        x, y = cols
        st.plotly_chart(bar_chart(df, x, y), key=f"b{i}")

    elif chart_type == "Line chart for time series":
        x, y = cols
        st.plotly_chart(line_chart(df, x, y), key=f"l{i}")

# ============================= #
# INSIGHTS
# ============================= #

st.subheader("🧠 Insights")

for i, txt in enumerate(generate_insights(df), 1):
    st.write(f"{i}. {txt}")

if st.button("Generate AI Insights"):
    st.write(generate_ai_insights(df))

# ============================= #
# SUMMARY
# ============================= #

st.subheader("📋 Summary")
st.write(df.describe())

st.subheader("📊 Types")
st.write(df.dtypes)

st.subheader("❗ Missing")

miss = df.isnull().sum()
st.write(pd.DataFrame({
    "Missing": miss,
    "Percent": (miss / len(df)) * 100
}))

# ============================= #
# AI CHAT WITH DATA
# ============================= #

st.subheader("💬 Chat with your Data")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat input (modern UI)
user_question = st.chat_input("Ask something about your data")

if user_question:
    with st.spinner("Thinking..."):
        answer = ask_ai_about_data(df, user_question, st.session_state.chat_history)

        st.session_state.chat_history.append(("You", user_question))
        st.session_state.chat_history.append(("AI", answer))

# Display chat
for sender, msg in st.session_state.chat_history:
    if sender == "You":
        st.markdown(f"**🧑 You:** {msg}")
    else:
        st.markdown(f"**🤖 AI:** {msg}")