from sqlalchemy import create_engine, text
import pandas as pd

def get_db_connection():
    return create_engine("postgresql://postgres:Sid1998@localhost:5432/autodatapipe")


def save_to_db(df, username):
    engine = get_db_connection()

    df = df.copy()
    df["username"] = username  # 🔥 attach user

    df.to_sql("datasets", engine, if_exists="append", index=False)


def load_user_datasets(username):
    engine = get_db_connection()

    query = text("""
        SELECT * FROM datasets 
        WHERE username = :username
        ORDER BY ingestion_time DESC
        LIMIT 100
    """)

    return pd.read_sql(query, engine, params={"username": username})