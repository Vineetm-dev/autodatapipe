import streamlit as st
import pandas as pd
import plotly.express as px
st.set_page_config(page_title="AutoDataPipe", page_icon="📊",  layout="wide")

# Dataset Intelligence Function

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
#____________
# App UI
#____________
st.title("AutoDataPipe - Universal Data Analysis Platform")

# Center upload section
col1, col2, col3, = st.columns([1,2,1])
with col2:
    uploaded_file = st.file_uploader("Upload your CSV dataset", type=["CSV"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    intelligence = dataset_intelligence(df)
    st.sidebar.title("Analysis Controls")
    analysis_mode = st.sidebar.selectbox("Choose Analysis Mode",[
        "Dataset Overview",
        "Automatic Charts",
        "Trend Analysis",
        "Category Comparison",
        "AI Insights"
    ])
    
    time_column = detect_time_column(df)
    country_column = detect_country_column(df)
    numeric_columns = detect_numeric_columns(df)

    if analysis_mode == "Dataset Overview":
        st.subheader("Raw Data Preview")
        st.write(df.head())

        st.subheader("Dataset Shape")
        st.write(f"Rows: {df.shape[0]}")
        st.write(f"Columns: {df.shape[1]}")

        st.subheader("Dataset Intelligence 🧠")
        st.write("Numeric Columns:", intelligence["numeric"])
        st.write("Categorical Columns:", intelligence["categorical"])
        st.write("Datetime Columns:", intelligence["datetime"])

        st.write("Possible Time Columns:", intelligence["time_guess"])
        st.write("Possible Country Columns:", intelligence["country_guess"])

        st.write("Detected Time Column:", time_column)
        st.write("Detected Country Column:", country_column)
        st.write("Detected Numeric metricss:", numeric_columns[:10])

    elif analysis_mode == "Automatic Charts":
        st.subheader("Automatic Charts 📊")
        numeric_cols = df.select_dtypes(include=["int64","Float64"]).columns
        categorical_cols = df.select_dtypes(include="object").columns

        time_cols = [col for col in df.columns if "year" in col.lower() or "date" in col.lower()]
        
        if len(time_cols) > 0 and len(numeric_cols) >0:
            time_col = time_cols[0]
            metrics = [col for col in numeric_cols if col != time_col]
            metric_choice = st.selectbox("Select metric to visualize against year", metrics)
            chart_date = df.groupby(time_col, as_index=False)[metric_choice].mean()
            fig = px.line(chart_date, x=time_col, y=metric_choice, title=f"{metric_choice} over time", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        if len(numeric_cols) > 0:
            metrics = numeric_cols[0]
            fig = px.histogram(df, x=metrics, nbins=40, title=f"Distribution of {metrics}", color_discrete_sequence=["cyan"])
            st.plotly_chart(fig)

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat = categorical_cols[0]
            num = numeric_cols[0]
            grouped = df.groupby(cat)[metrics].mean().reset_index()
            top = grouped.sort_values(metrics, ascending=False).head(15)
            fig = px.bar(grouped, x=cat, y=metrics, title=f"Top {cat} by {metrics}", color=metrics)
            st.plotly_chart(fig)
        
        if len(numeric_cols) >=2:
            fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=f"{numeric_cols[0]} vs {numeric_cols[1]}", color=numeric_cols[1])
            st.plotly_chart(fig)
    
    elif analysis_mode == "Trend Analysis":
        
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
            
            # metrics Selector
            st.subheader("Select metrics 📊")
            numeric_columns = filtered_df.select_dtypes(include=["int64", "float64"]).columns
            numeric_columns = [col for col in numeric_columns if col != date_column]
            selected_metrics = st.selectbox("Choose a metrics", numeric_columns)

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
                value = year_filtered[selected_metrics].values[0]
                st.write(f"{selected_metrics} for {selected_countries[0]} in {selected_year} = {value}")
                
                # Trend Graph
                st.subheader("Trend Over Time ⌛")
                st.line_chart(filtered_df.pivot(index=date_column, columns="country", values=selected_metrics))

            # Automatic Data Dashboard
            st.subheader("Automatic Data Dashboard 📊")
            auto_metricss = filtered_df.select_dtypes(include=["int64", "float64"]).columns
            auto_metricss = [col for col in auto_metricss if col != date_column]

            auto_metricss = auto_metricss[:6]
            for metrics in auto_metricss:
                st.write(f"{metrics} over time")
                chart_date = filtered_df.set_index(date_column)[metrics]
                fig = px.line(chart_date, title=f"{metrics} over time")
                st.plotly_chart(fig)

            #Growth % Calculation
            st.subheader("Growth % Analysis 📈")

    elif analysis_mode == "Category Comparison":
        st.subheader("Category Comparison📊")

        categorical_columns = df.select_dtypes(include="object").columns

        numeric_columns = df.select_dtypes(include=["Int64","Float64"]).columns

        category_column = st.selectbox("Choose a category column", categorical_columns)

        metrics_column = df.select_dtypes(include=["Int64", "Float64"]).columns
        metrics_column = st.selectbox("Choose a metrics column", numeric_columns)

        comparison_data = df.groupby(category_column)[metrics_column].mean()

        comparison_data = comparison_data.sort_values(ascending=False)

        st.write("Comparison Table")
        st.write(comparison_data)

        fig = px.bar(comparison_data, labels={"value": metrics_column,"index": category_column}, title=f"{metrics_column} by {category_column}")
        st.plotly_chart(fig)
    
    elif analysis_mode == "AI Insights":
        st.subheader("AI Dataset Insights 🧠")
        rows, cols = df.shape
        st.write(f"Dataset contains **{rows} rows** and **{cols} columns**.")
        numeric_cols = df.select_dtypes(include=["Int64","Float64"]).columns
        categorical_cols = df.select_dtypes(include=["object"]).columns

        st.write(f"Detected **{len(numeric_cols)} numeric features**.")
        st.write(f"Detected **{len(categorical_cols)} categorical features**.")

        missing = df.isnull().sum()
        missing_percent = (missing / len(df)) * 100

        high_missing = missing_percent[missing_percent > 30]

        if len(high_missing) > 0:
            st.write("⚠️ Columns with high missing values (>30):")
            st.write(high_missing.sort_values(ascending=False))
        else:
            st.write("No major missing data issues detected.")
        
        time_cols = [col for col in df.columns if "year" in col.lower() or "date" in col.lower()]
        
        if len(time_cols) > 0 and len(numeric_cols) > 1:
            time_col = time_cols[0]
            metrics = [col for col in numeric_cols if col not in time_cols]
            if len(metrics) > 0:
                metric = metrics[0]
                trend = df.groupby(time_col)[metric].mean()
                start_val = trend.iloc[0]
                end_val = trend.iloc[-1]
                if start_val !=0 :
                    growth = ((end_val - start_val) / start_val) * 100
                    st.write(f"✅ **{metric} increased by approximately {growth: .2f} % from {trend.index.min()} to {trend.index.max()}**")

        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            cat = categorical_cols[0]
            metric = numeric_cols[0]
            top = df.groupby(cat)[metric].mean().sort_values(ascending=False).head(5)

            st.write(f"🏆 Top categories based on **{metric}**.")
            st.write(top)           

    
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

    