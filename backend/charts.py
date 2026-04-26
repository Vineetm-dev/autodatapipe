import plotly.express as px

def recommended_charts(df):
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    
    recommendations = []
    if len(numeric_cols) >= 1:
        recommendations.append(("Histogram for numeric columns", numeric_cols[0]))

    if len(numeric_cols) >= 2:
        recommendations.append(("Scatter plot for numeric columns", (numeric_cols[0], numeric_cols[1])))
    
    if categorical_cols and numeric_cols:
        recommendations.append(("Bar chart for category vs metric", (categorical_cols[0], numeric_cols[0])))
    
    if datetime_cols and numeric_cols:
        recommendations.append(("Line chart for time series", (datetime_cols[0], numeric_cols[0])))

    return recommendations

def histogram_chart(df, col):
    return px.histogram(df, x=col)

def bar_chart(df, category, metric):
    grouped = df.groupby(category)[metric].mean().reset_index()
    return px.bar(grouped, x=category, y=metric)

def scatter_chart(df, x, y):
    return px.scatter(df, x=x, y=y)

def line_chart(df, time_col, metric):
    grouped = df.groupby(time_col)[metric].mean().reset_index()
    return px.line(grouped, x=time_col, y=metric)