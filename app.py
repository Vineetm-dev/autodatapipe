import streamlit as st
import pandas as pd

# Dataset Intelligence Function

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
#____________
# App UI
#____________
st.title("AutoDataPipe - Universal CSV ETL Engine")

uploaded_file = st.file_uploader("Upload a CSV file", type=["CSV"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    time_column = detect_time_column(df)
    country_column = detect_country_column(df)
    numeric_columns = detect_country_column(df)

    st.subheader("Raw Data Preview")
    st.write(df.head())

    st.subheader("Dataset Shape 📐")
    st.write(f"Rows: {df.shape[0]}")
    st.write(f"Columns: {df.shape[1]}")

    st.subheader("Dataset Intelligence 🧠")
    st.write("Detected Time Column:", time_column)
    st.write("Detected Country Column:", country_column)
    st.write("Detected Numeric Metrics:", numeric_columns[:10])

    st.subheader("Column Data Types 🧠")
    st.write(df.dtypes)

    st.subheader("Missing Values Report 🔍")
    missing = df.isnull().sum()
    missing_percent = (missing / len(df)) * 100
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

    st.subheader("Trend Analysis Setup 📊")

    
    
    date_column = st.selectbox("Select a date column (if available)", ["None"] + list(df.columns))
    
    if date_column != "None":

        # Prepare Time Data
        df_sorted = df.copy()
        df_sorted[date_column] = pd.to_numeric(df_sorted[date_column], errors="coerce")
        df_sorted = df_sorted.dropna(subset=[date_column])
        df_sorted = df_sorted.sort_values(by=date_column).reset_index(drop=True)


        # Country Selector
        st.subheader("Select Country 🌍")
        unique_countries = sorted(df_sorted["country"].unique())
        selected_countries = st.multiselect("Choose a country (max 2)", unique_countries, default=[unique_countries[0]])

        # Filter By Country
        filtered_df = df_sorted[df_sorted["country"].isin(selected_countries)]
        
        # Metric Selector
        st.subheader("Select Metric 📊")
        numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns
        numeric_columns = [col for col in numeric_columns if col != date_column]
        selected_metric = st.selectbox("Choose a metric", numeric_columns)

        # Year Range Slider
        min_year = int(filtered_df[date_column].min())
        max_year = int(filtered_df[date_column].max())
        year_range = st.slider("Select year range", min_year, max_year,(min_year,max_year))

        filtered_df = filtered_df[(filtered_df[date_column] >= year_range[0]) & (filtered_df[date_column] <= year_range[1])]

        
       # Year Selector 
        st.subheader("Select Year (optional) 🗓️")
        available_year = sorted(filtered_df[date_column].unique())
        selected_year = st.selectbox("Choose a year", available_year)

       
        # Show Value for Selected Year
        st.subheader("Selected Value 📌")

        year_filtered = filtered_df[filtered_df[date_column] == selected_year]
        if not year_filtered.empty:
            value = year_filtered[selected_metric].values[0]
            st.write(f"{selected_metric} for {selected_countries[0]} in {selected_year} = {value}")
            
            # Trend Graph
            st.subheader("Trend Over Time ⌛")
            st.line_chart(filtered_df.pivot(index=date_column, columns="country", values=selected_metric))

        # Automatic Data Dashboard
        st.subheader("Automatic Data Dashboard 📊")
        auto_matrics = filtered_df.select_dtypes(include=["int64", "float64"]).columns
        auto_matrics = [col for col in auto_matrics if col != date_column]

        auto_matrics = auto_matrics[:6]
        for metric in auto_matrics:
            st.write(f"{metric} over time")
            chart_date = filtered_df.set_index(date_column)[metric]
            st.line_chart(chart_date)

        #Growth % Calculation
        st.subheader("Growth % Analysis 📈")