import pandas as pd

def read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def save_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)
