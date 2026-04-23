import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import requests
import logging
from openai import OpenAI
import os
from dotenv import load_dotenv

if "df" not in st.session_state:
    st.session_state.df = None
df = st.session_state.df

st.markdown("""<style>
        .stMetric {
            background-color: #111;
            padding: 10px;
            border-radius: 10px;}
        </style>""", unsafe_allow_html=True)



load_dotenv()
client = OpenAI()

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="AutoDataPipe", page_icon="📊",  layout="wide")

# Dataset Intelligence Function
@st.cache_data
def generate_ai_insights(df):
    try:
        Sample_data = df.head(20).to_csv(index=False)
        prompt = f"""you are a senior data analyst. Analyze this dataset and provide:
        - What the dataset represents
        - Key trends
        - Interesting insights
        Dataset: {Sample_data}"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception:
        return "⚠️ AI insights unavailable (quota limit reached). Please try again later! ⚠️"

def ask_ai_about_data(df, question):
    try:
        sample_data = df.head(50).to_csv(index=False)
        prompt = f"""you are a data analyst. Dataset: {sample_data}. Question: {question} Answer clearly using the dataset."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error asking AI about data: {str(e)}"

def load_data(file):
    return pd.read_csv(file)

def get_db_connection():
    engine = create_engine("postgresql://postgres:Sid1998@localhost:5432/autodatapipe")
    return engine

def save_to_db(df):
    engine = get_db_connection()
    df.to_sql("datasets", engine, if_exists="replace", index=False)

def load_from_db():
    engine = get_db_connection()
    df = pd.read_sql("""SELECT * FROM datasets ORDER BY ingestion_time DESC LIMIT 100""", engine)
    return df

def clean_data(df):
    try:
        df = df.drop_duplicates()
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"Error during cleaning: {e}")
        return df

def process_data(df):

    return df

def dataset_intelligence(df):
    numeric_columns = df.select_dtypes(include=["int64","float64"]).columns.tolist()

    categorical_columns = df.select_dtypes(include=["object"]).columns.tolist()

    datetime_columns = df.select_dtypes(include=["datetime64"]).columns.tolist()

    possible_time_columns = [
        col for col in df.columns
        if "year" in col.lower()
        or "date" in col.lower()
        or "time" in col.lower()
        ]
    possible_country_columns = [
        col for col in df.columns
        if "country" in col.lower()
        or "nation" in col.lower()
        or "state" in col.lower()
        or "region" in col.lower()
        ]

    return {
        "numeric": numeric_columns,
        "categorical": categorical_columns,
        "datetime": datetime_columns,
        "time_guess": possible_time_columns,
        "country_guess": possible_country_columns
        }


def detect_time_column(df):
    possible_time_names = ["year","date","time","month"]
    for col in df.columns:
        if col.lower() in possible_time_names:
            return col
    return None

def detect_country_column(df):
    possible_names = ["country","nation","location","state"]
    for col in df.columns:
        if col.lower() in possible_names:
            return col

    return None

def detect_numeric_columns(df):
    numeric_cols = df.select_dtypes(include=["int64","float64"]).columns
    return list(numeric_cols)

def generate_insights(df):
    insights = []
    #basic stats #
    rows, cols = df.shape
    insights.append(f"Dataset contains {rows} rows and {cols} columns.")

    #missing values #
    missing = df.isnull().sum().sum()
    insights.append(f"There are {missing} missing values in the dataset.")
    return insights

    #numeric analysis #
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) > 0:
        top_col = df[numeric_cols].mean().idxmax()
        insights.append(f"'{top_col}' has the highest average value.")


    # category dominance #
    categorical_cols = df.select_dtypes(include=["object"]).columns
    if len(categorical_cols) > 0:
        cat_col = categorical_cols[0]
        top_category = df[cat_col].value_counts().idxmax()
        insights.append(f"Most frequent category in '{cat_col}' is '{top_category}'.")

    # time trends #
    time_cols = [col for col in df.columns if "year" in col.lower() or "date" in col.lower()]
    if time_cols and len(numeric_cols) > 0:
        time_col = time_cols[0]
        metric = numeric_cols[0]
        trend = df.groupby(time_col)[metric].mean()
        if len(trend) > 1:
            if trend.iloc[-1] > trend.iloc[0]:
                insights.append(f"{metric} shows an increasing trend over time.")
            else:
                insights.append(f"{metric} shows a decreasing trend over time.")
    

def extract_data(file=None, api_data=None):
    if file is not None:
        return pd.read_csv(file)
    elif api_data is not None:
        return pd.DataFrame(api_data)
    return None

def transform_data(df, source = "CSV"):
    df = clean_data(df)

# metadata #
    df["ingestion_time"] = pd.Timestamp.utcnow()
    df["source"] = source
    return df

def load_data_pipeline(df):
    save_to_db(df)

def run_etl(file=None, api_data=None, source="CSV"):
    df = extract_data(file, api_data)
    df = transform_data(df, source)
    load_data_pipeline(df)
    return df

def fetch_api_data():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame([{"asset": "bitcoin", "usd_price": data["bitcoin"]["usd"], "timestamp": pd.Timestamp.now()}])
            return df
        else:
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

def run_full_pipeline(df):
    st.info("Running full ETL pipeline...")

    # extract #
    raw_df = df.copy()

    # transform #
    cleaned_df = clean_data(raw_df)

    # load #
    save_to_db(cleaned_df)
    st.success("ETL pipeline completed")

    return cleaned_df
#____________
# App UI
#____________
st.set_page_config(layout="wide", page_title="AutoDataPipe", page_icon="📊")

st.markdown("""
<style>
/* Main background */
[data-testid="stAppViewContainer"] {
background: linear-gradient(135deg, #0f172a, #2061f7);
}
/* Glass cards */
.block-container {
padding: 2rem;
}
/* Card style */
div[data-testid="metric-container"],
div[data-testid="stPlotlyChart"],{
background: rgba(255, 255, 255, 0.05);
border-radius: 15px;
padding: 15px;
backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.1);
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
/*Buttons*/
.stButton button {
background: linear-gradient(135deg, #06b6d4, #3b82f6);
color: white;
border-radius: 10px;
border: none;}
</style>
""", unsafe_allow_html=True)

st.title("AutoDataPipe: Your AI Dashboard 📊🤖")
st.markdown("### Turn any CSV dataset into insights instantly 🚀")
st.markdown("---")

# Data source selection #
data_source = st.radio("Select Data Source", ["Upload CSV", "Fetch API Data"])

# CSV Option #
if data_source == "Upload CSV":
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
        if uploaded_file is not None:
            st.session_state.df = run_etl(file=uploaded_file, source="CSV")
            st.success("CSV file uploaded and processed successfully!")

# API Option #
elif data_source == "Use API":
    if st.button("Fetch API Data", key="fetch_api_button"):
        api_df = fetch_api_data()
        if api_df is not None:
            st.session_state.df = run_etl(api_data=api_df, source="API")
            st.success("API data fetched and processed successfully!")
        else:
            st.error("Failed to fetch API data. Please try again later.")

    
df = st.session_state.df
if df is None:
    st.info("Upload a CSV or fetch API data to get started!")
    st.stop()

    
    df = st.session_state.df
    if df is not None:
        rows, cols = df.shape
        st.write(rows, cols)

    df = st.session_state.df
    if df is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rows", df.shape[0])
        col2.metric("Columns", df.shape[1])
        col3.metric("Missing Values", int(df.isnull().sum().sum()))
        col4.metric("Duplicates", int(df.duplicated().sum()))

# mutli chart dashboard #
st.subheader("Smart Dashboard 📊")
col1, col2 = st.columns(2)

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
main_metric = None
if numeric_cols:
    main_metric = st.selectbox("Select Metric", numeric_cols, key="main_metric_select")

categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
category = None
if categorical_cols:
    category = st.selectbox("Select Category", categorical_cols, key="category_select")

#histogram #
with col1:
    if main_metric:
        fig1 = px.histogram(st.session_state.df, x=main_metric, nbins=40, color_discrete_sequence=["cyan"])
        fig1.update_layout(template="plotly_dark", transition_duration=800, transition_easing="cubic-in-out")
        st.plotly_chart(fig1, use_container_width=True, key="hist_chart")

# Bar chart #
with col2:
    if category and main_metric:
        grouped = st.session_state.df.groupby(category)[main_metric].mean().reset_index()
        top = grouped.sort_values(main_metric, ascending=False).head(10)
        fig2 = px.bar(top, x=category, y=main_metric, color=main_metric, color_continuous_scale="blues")
        fig2.update_layout(template="plotly_dark", transition_duration=800, transition_easing="cubic-in-out")
        st.plotly_chart(fig2, use_container_width=True, key="bar_chart")


#detect time column #
time_cols = [col for col in st.session_state.df.columns if any(x in col.lower() for x in ["year","date","time","timestamp"])]
time_col = time_cols[0] if time_cols else None

# LINE CHART (TIME SERIES CHART) #
st.subheader("Time Over Time ⌛")
if time_col and main_metric:
    df_grouped = st.session_state.df.groupby(time_col, as_index=False)[main_metric].mean()
    st.write("Preview of grouped data:", df_grouped.head())
else:
    st.warning("No time column detected or no metric selected for time series chart.")

st.subheader("🧠 AI Insights & Summary")
insights = []

#1. missing values insight #
missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
insights.append(f"Dataset has {missing_pct:.2f}% missing values.")

#2.highest average column #
numeric_cols = df.select_dtypes(include=["number"]).columns
if len(numeric_cols) > 0:
    top_col = df[numeric_cols].mean().idxmax()
    insights.append(f"'{top_col}' has the highest average value.")

#3.trend insight #
if time_col  and main_metric:
    df_grouped = st.session_state.df.groupby(time_col, as_index=False)[main_metric].mean()
    trend = df_grouped[main_metric].iloc[-1] - df_grouped[main_metric].iloc[0]
    direction = "increasing" if trend > 0 else "decreasing"
    st.write(f"{main_metric} shows an overall {direction} trend over time.")
else:
    st.warning("No valid time column or metric selected for trend analysis.")

#4. display insights #
for i, insight in enumerate(insights, 1):
    st.write(f"{i}. {insight}")

# STORY #
st.subheader("Data Storytelling 📖")

summary = f""" This dataset contains {st.session_state.df.shape[0]} rows and {st.session_state.df.shape[1]} columns.
                It includes both numerical and categorical variable, suitable for analysis"""

st.write(summary)



left, centre, right = st.columns([1,2,1])

with left:
    st.subheader("⏹️ Filters")
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    selected_metrics = st.selectbox("Select Metric", numeric_cols, key="metric1")
    selected_category = None
    if categorical_cols:
        selected_category = st.selectbox("Select Category", categorical_cols, key="category1")
    
with centre:
    st.subheader("📊 Data Visualization")

    import plotly.express as px
    figi1 = px.histogram(st.session_state.df, x=selected_metrics, nbins=40, color_discrete_sequence=["cyan"])
    figi1.update_layout(template="plotly_dark", transition_duration=800, transition_easing="cubic-in-out")
    st.plotly_chart(figi1, use_container_width=True)

    if len(numeric_cols) >= 2:
        figi2 = px.scatter(st.session_state.df, x=numeric_cols[0], y=numeric_cols[1], color=numeric_cols[1])
        figi2.update_layout(template="plotly_dark", transition_duration=800, transition_easing="cubic-in-out")
        st.plotly_chart(figi2, use_container_width=True)

    if selected_category:
        grouped = st.session_state.df.groupby(selected_category)[selected_metrics].mean().reset_index()
        figi3 = px.bar(grouped, x=selected_category, y=selected_metrics, color=selected_metrics)
        figi3.update_layout(template="plotly_dark", transition_duration=800, transition_easing="cubic-in-out")
        st.plotly_chart(figi3, use_container_width=True)

with right:
    st.subheader("🤖 AI Insights")
    if st.button("Generate AI Insights", key="ai_insights_button"):
        with st.spinner("Analyzing dataset..."):
            insights = generate_ai_insights(st.session_state.df)
            st.success(insights)


logging.info("Dataset processed successfully")

st.subheader("Column Data Types 🧠")
st.write(st.session_state.df.dtypes)

st.subheader("Missing Values Report 🔍")
missing = st.session_state.df.isnull().sum()
missing_percent = (missing / len(st.session_state.df)) * 100
missing_df = pd.DataFrame({
    "Missing Values" : missing,
    "Missing Percentage (%)" : missing_percent
})
st.write(missing_df.columns)
filtered_missing = missing_df[missing_df["Missing Values"] > 0]

if not filtered_missing.empty:
    st.write(filtered_missing)
else:
    st.write("No missing values found 💐")

st.subheader("Column Type Classification 🧠")
numeric_cols = df.select_dtypes(include=["int64","float64"]).columns
categorical_cols = df.select_dtypes(include=["object"]).columns
datetime_cols = df.select_dtypes(include=["datetime64"]).columns

st.write("Numeric Columns:", list(numeric_cols))
st.write("Categorical Columns:", list(categorical_cols))
st.write("Datatime Columns:", list(datetime_cols))

    

# auto detection of column types and main metric/category#
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
main_metric = numeric_cols[0] if numeric_cols else None
category = categorical_cols[0] if categorical_cols else None

st.download_button("Download Clean Data", st.session_state.df.to_csv(index=False).encode('utf-8'), "cleaned_data.csv", "text/csv")

if st.button("Save Data to Database", key="save_db_button"):
    save_to_db(st.session_state.df)
    st.success("Saved to database ✅")

if st.button("Load Data from Database", key="load_db_button"):
    db_df = load_from_db()
    st.write("Data loaded from database:")
    st.write(db_df.head())

##OLD SIDEBAR CODE##
#_________________#

# st.sidebar.subheader("Data Processing ⚙️")

# if st.sidebar.button("Clean Dataset"):
#     df = clean_data(df)
#     st.sidebar.success("Dataset cleaned successfully ✅")

# csv = df.to_csv(index=False).encode('utf-8')
# st.sidebar.download_button(label="Download Processed Data 🗃️", data=csv, file_name="Processed_data.csv", mime="text/csv")

# intelligence = dataset_intelligence(df)
# st.sidebar.title("Analysis Controls")
# analysis_mode = st.sidebar.selectbox("Choose Analysis Mode",[
#     "Dataset Overview",
#     "Automatic Charts",
#     "Trend Analysis",
#     "Category Comparison",
#     "AI Insights"
# ])

# time_column = detect_time_column(df)
# country_column = detect_country_column(df)
# numeric_columns = detect_numeric_columns(df)

# if analysis_mode == "Dataset Overview":
#     st.subheader("Raw Data Preview")
#     st.write(df.head())

#     st.subheader("Dataset Shape")
#     st.write(f"Rows: {df.shape[0]}")
#     st.write(f"Columns: {df.shape[1]}")

#     st.subheader("Dataset Intelligence 🧠")
#     st.write("Numeric Columns:", intelligence["numeric"])
#     st.write("Categorical Columns:", intelligence["categorical"])
#     st.write("Datetime Columns:", intelligence["datetime"])

#     st.write("Possible Time Columns:", intelligence["time_guess"])
#     st.write("Possible Country Columns:", intelligence["country_guess"])

#     st.write("Detected Time Column:", time_column)
#     st.write("Detected Country Column:", country_column)
#     st.write("Detected Numeric metricss:", numeric_columns[:10])

# elif analysis_mode == "Automatic Charts":
#     st.subheader("Automatic Charts 📊")
#     numeric_cols = df.select_dtypes(include=["int64","Float64"]).columns
#     categorical_cols = df.select_dtypes(include="object").columns

#     time_cols = [col for col in df.columns if "year" in col.lower() or "date" in col.lower()]
    
#     if len(time_cols) > 0 and len(numeric_cols) >0:
#         time_col = time_cols[0]
#         metrics = [col for col in numeric_cols if col != time_col]
#         metric_choice = st.selectbox("Select metric to visualize against year", metrics)
#         chart_date = df.groupby(time_col, as_index=False)[metric_choice].mean()
#         fig = px.line(chart_date, x=time_col, y=metric_choice, title=f"{metric_choice} over time", markers=True)
#         st.plotly_chart(fig, use_container_width=True)
#     if len(numeric_cols) > 0:
#         metrics = numeric_cols[0]
#         fig = px.histogram(df, x=metrics, nbins=40, title=f"Distribution of {metrics}", color_discrete_sequence=["cyan"])
#         st.plotly_chart(fig)

#     if len(categorical_cols) > 0 and len(numeric_cols) > 0:
#         cat = categorical_cols[0]
#         num = numeric_cols[0]
#         grouped = df.groupby(cat)[metrics].mean().reset_index()
#         top = grouped.sort_values(metrics, ascending=False).head(15)
#         fig = px.bar(grouped, x=cat, y=metrics, title=f"Top {cat} by {metrics}", color=metrics)
#         st.plotly_chart(fig)
    
#     if len(numeric_cols) >=2:
#         fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=f"{numeric_cols[0]} vs {numeric_cols[1]}", color=numeric_cols[1])
#         st.plotly_chart(fig)

# elif analysis_mode == "Trend Analysis":
    
#     st.subheader("Trend Analysis Setup 📊")



#     date_column = st.selectbox("Select a date column (if available)", ["None"] + list(df.columns))
    
#     if date_column != "None":

#         # Prepare Time Data
#         df_sorted = df.copy()
#         df_sorted[date_column] = pd.to_numeric(df_sorted[date_column], errors="coerce")
#         df_sorted = df_sorted.dropna(subset=[date_column])
#         df_sorted = df_sorted.sort_values(by=date_column).reset_index(drop=True)


#         # Country Selector
#         st.subheader("Select Country 🌍")
#         country_column = detect_country_column(df_sorted)
#         if country_column:
#             unique_countries = sorted(df_sorted[country_column].dropna().unique())
#         else:
#             st.warning("No country column detected")
#             unique_countries = []
#         selected_countries = st.multiselect("Choose a country (max 2)", unique_countries, default=[unique_countries[0]])

#         # Filter By Country
#         filtered_df = df_sorted[df_sorted[country_column].isin(selected_countries)]
        
#         # metrics Selector
#         st.subheader("Select metrics 📊")
#         numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns
#         numeric_columns = [col for col in numeric_columns if col != date_column]
#         selected_metrics = st.selectbox("Choose a metrics", numeric_columns)

#         # Year Range Slider
#         min_year = int(filtered_df[date_column].min())
#         max_year = int(filtered_df[date_column].max())
#         year_range = st.slider("Select year range", min_year, max_year,(min_year,max_year))

#         filtered_df = filtered_df[(filtered_df[date_column] >= year_range[0]) & (filtered_df[date_column] <= year_range[1])]

        
#     # Year Selector 
#         st.subheader("Select Year (optional) 🗓️")
#         available_year = sorted(filtered_df[date_column].unique())
#         selected_year = st.selectbox("Choose a year", available_year)

    
#         # Show Value for Selected Year
#         st.subheader("Selected Value 📌")

#         year_filtered = filtered_df[filtered_df[date_column] == selected_year]
#         if not year_filtered.empty:
#             value = year_filtered[selected_metrics].values[0]
#             st.write(f"{selected_metrics} for {selected_countries[0]} in {selected_year} = {value}")
            
#             # Trend Graph
#             st.subheader("Trend Over Time ⌛")
#             st.line_chart(filtered_df.pivot(index=date_column, columns="country", values=selected_metrics))

#         # Automatic Data Dashboard
#         st.subheader("Automatic Data Dashboard 📊")
#         auto_metricss = filtered_df.select_dtypes(include=["int64", "float64"]).columns
#         auto_metricss = [col for col in auto_metricss if col != date_column]

#         auto_metricss = auto_metricss[:6]
#         for metrics in auto_metricss:
#             st.write(f"{metrics} over time")
#             chart_date = filtered_df.set_index(date_column)[metrics]
#             fig = px.line(chart_date, title=f"{metrics} over time")
#             st.plotly_chart(fig)

#         #Growth % Calculation
#         st.subheader("Growth % Analysis 📈")

# elif analysis_mode == "Category Comparison":
#     st.subheader("Category Comparison📊")

#     categorical_columns = df.select_dtypes(include="object").columns

#     numeric_columns = df.select_dtypes(include=["Int64","Float64"]).columns

#     category_column = st.selectbox("Choose a category column", categorical_columns)

#     metrics_column = df.select_dtypes(include=["Int64", "Float64"]).columns
#     metrics_column = st.selectbox("Choose a metrics column", numeric_columns)

#     comparison_data = df.groupby(category_column)[metrics_column].mean()

#     comparison_data = comparison_data.sort_values(ascending=False)

#     st.write("Comparison Table")
#     st.write(comparison_data)

#     fig = px.bar(comparison_data, labels={"value": metrics_column,"index": category_column}, title=f"{metrics_column} by {category_column}")
#     st.plotly_chart(fig)

# elif analysis_mode == "AI Insights":

#     st.subheader("AI Dataset Insights 🤖")
#     st.info("⚠️ AI insights use limited API quotas. Use wisely! ⚠️")

#     #Generate AI Insights
#     if st.button("Generate AI Insights"):
#         with st.spinner("Analyzing dataset"):
#             insights = generate_ai_insights(df)
#             st.write(insights)
#     st.success("AI Powered Insights Enabled 🚀")

#     #Ask AI Questions about data
#     st.subheader("Ask Questions About Your Data ❓")
#     user_question = st.text_input("Ask anything about your dataset")
#     if st.button("Ask AI"):
#         if user_question:
#             with st.spinner("Thinking..."):
#                 answer = ask_ai_about_data(df, user_question)
#                 st.write(answer)

## OLD SIDEBAR CODE END ##
#_________________#


