import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

# -----------------------------
# PATHS FOR LOCAL HISTORY STORAGE
# -----------------------------
HISTORY_DIR = "history"
CLEANED_FILES_DIR = os.path.join(HISTORY_DIR, "cleaned_files")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")

os.makedirs(CLEANED_FILES_DIR, exist_ok=True)
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

# -----------------------------
# SAVE HISTORY ENTRY
# -----------------------------
def save_history(filename, actions, cleaned_df):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cleaned_file_path = os.path.join(
        CLEANED_FILES_DIR,
        f"{os.path.splitext(filename)[0]}_cleaned_{int(datetime.now().timestamp())}.csv"
    )
    cleaned_df.to_csv(cleaned_file_path, index=False)

    history_entry = {
        "filename": filename,
        "timestamp": timestamp,
        "actions": actions,
        "cleaned_file": cleaned_file_path,
        "rows": len(cleaned_df),
        "columns": list(cleaned_df.columns)
    }

    with open(HISTORY_FILE, "r+") as f:
        history = json.load(f)
        history.append(history_entry)
        f.seek(0)
        json.dump(history, f, indent=4)

# -----------------------------
# AUTO-CLEAN FUNCTION
# -----------------------------
def auto_clean(df):
    actions = []

    # Remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        actions.append(f"Removed {before - after} duplicate rows.")

    # Fill missing numeric values with mean
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mean())
            actions.append(f"Filled missing numeric values in '{col}' with mean.")

    # Fill missing categorical values with mode
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mode()[0])
            actions.append(f"Filled missing categorical values in '{col}' with mode.")

    # Strip spaces in string columns
    for col in cat_cols:
        df[col] = df[col].astype(str).str.strip()

    actions.append("Auto-clean completed.")

    return df, actions

# -----------------------------
# DATA QUALITY REPORT
# -----------------------------
def quality_report(df):
    st.subheader("📊 Data Quality Report")

    st.write("### Missing Values per Column")
    st.bar_chart(df.isna().sum())

    st.write("### Data Types")
    st.dataframe(df.dtypes.to_frame("dtype"))

    st.write("### Duplicate Rows")
    st.write(f"Total duplicates: **{df.duplicated().sum()}**")

    st.write("### Basic Statistics")
    st.dataframe(df.describe(include="all"))

# -----------------------------
# COLUMN LEVEL CLEANING
# -----------------------------
def column_tools(df):
    st.subheader("🧰 Column-Level Cleaning Tools")

    col = st.selectbox("Select a column to modify:", df.columns)

    action = st.radio(
        "Choose an operation:",
        ["Rename column", "Drop column", "Convert to datetime", "Apply custom formula"]
    )

    if action == "Rename column":
        new_name = st.text_input("Enter new column name:")
        if st.button("Rename"):
            df.rename(columns={col: new_name}, inplace=True)
            st.success(f"Column '{col}' renamed to '{new_name}'")

    elif action == "Drop column":
        if st.button("Drop"):
            df.drop(columns=[col], inplace=True)
            st.success(f"Dropped column '{col}'")

    elif action == "Convert to datetime":
        if st.button("Convert"):
            df[col] = pd.to_datetime(df[col], errors='coerce')
            st.success(f"Converted '{col}' to datetime format")

    elif action == "Apply custom formula":
        st.write("Example: `value.lower()`, `value.replace('-', '')`")
        formula = st.text_input("Enter a Python expression using 'value':")
        if st.button("Apply"):
            try:
                df[col] = df[col].apply(lambda value: eval(formula))
                st.success("Formula applied successfully!")
            except:
                st.error("Invalid formula.")

    return df

# -----------------------------
# VIEW HISTORY PAGE
# -----------------------------
def view_history():
    st.title("📁 Cleaning History")

    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    if len(history) == 0:
        st.info("No cleaning history yet.")
        return

    for entry in history:
        st.markdown("### ✅ Cleaned File:")
        st.write(f"**File:** {entry['filename']}")
        st.write(f"**Timestamp:** {entry['timestamp']}")
        st.write(f"**Rows:** {entry['rows']}")
        st.write(f"**Columns:** {entry['columns']}")
        st.write(f"**Actions:**")
        for a in entry["actions"]:
            st.write(f"- {a}")

        with open(entry["cleaned_file"], "rb") as f:
            st.download_button(
                label="Download Cleaned File",
                data=f,
                file_name=os.path.basename(entry["cleaned_file"]),
                mime="text/csv"
            )
        st.write("---")

# -----------------------------
# MAIN UI
# -----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Upload & Clean", "Cleaning History"])

if page == "Cleaning History":
    view_history()
    st.stop()

st.title("🧼 CSV Data Cleaning Tool (Enhanced Version)")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())

    st.write("---")

    # Auto clean
    if st.button("⚡ Auto Clean Dataset"):
        cleaned, actions = auto_clean(df.copy())
        st.dataframe(cleaned.head())
        save_history(uploaded_file.name, actions, cleaned)
        st.success("Auto-clean completed and saved to history!")

    st.write("---")

    # Data Quality Report
    if st.checkbox("Show Data Quality Report"):
        quality_report(df)

    st.write("---")

    # Column cleaning tools
    st.write("### Advanced Column Tools")
    df = column_tools(df)

    # Download cleaned file
    st.write("---")
    st.write("### Download Final Cleaned File")
    csv = df.to_csv(index=False).encode()
    st.download_button("Download", data=csv, file_name="cleaned_output.csv", mime="text/csv")

