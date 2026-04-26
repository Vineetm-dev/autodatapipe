import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)


def extract_data(file=None, api_data=None):
    if file is not None:
        logging.info("Reading CSV file...")
        return pd.read_csv(file)

    elif api_data is not None:
        logging.info("Processing API data...")

        # Handle both dict and DataFrame safely
        if isinstance(api_data, pd.DataFrame):
            return api_data
        else:
            return pd.DataFrame(api_data)

    return None


def clean_data(df):
    if df is None:
        raise ValueError("clean_data received None")

    logging.info("Cleaning data...")

    df = df.drop_duplicates()
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)

    return df


def transform_data(df, source="CSV"):
    if df is None:
        raise ValueError("transform_data received None")

    logging.info("Transforming data...")

    df = clean_data(df)

    df["ingestion_time"] = pd.Timestamp.utcnow()
    df["source"] = source

    return df


def run_etl(file=None, api_data=None, source="CSV"):
    logging.info("Running ETL pipeline...")

    df = extract_data(file, api_data)

    if df is None:
        raise ValueError("No data extracted")

    df = transform_data(df, source)

    if df is None:
        raise ValueError("Transformation failed")

    logging.info("ETL completed successfully")

    return df