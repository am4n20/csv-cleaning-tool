import pandas as pd

def auto_clean(df: pd.DataFrame):
    actions = []

    # drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    if len(df) != before:
        actions.append("Removed duplicate rows")

    # fill missing values
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].fillna("Unknown")
        else:
            df[col] = df[col].fillna(df[col].median())

    actions.append("Filled missing values")
    return df, actions
