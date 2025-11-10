import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
from datetime import datetime

# -----------------------------
# CONNECT TO DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect("outputs.db", check_same_thread=False)
    cursor = conn.cursor()

    # Create table to store history + cleaned CSV content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clean_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            timestamp TEXT,
            actions TEXT,
            rows INTEGER,
            columns TEXT,
            cleaned_csv TEXT
        )
    """)

    conn.commit()
    return conn


conn = init_db()


# -----------------------------
# SAVE HISTORY + CLEANED CSV TO DATABASE
# -----------------------------
def save_to_db(filename, actions, cleaned_df):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cleaned_csv_text = cleaned_df.to_csv(index=False)

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clean_history
        (filename, timestamp, actions, rows, columns, cleaned_csv)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        filename,
        timestamp,
        json.dumps(actions),
        len(cleaned_df),
        json.dumps(list(cleaned_df.columns)),
        cleaned_csv_text
    ))

    conn.commit()


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

    # Fill missing numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mean())
            actions.append(f"Filled missing numeric values in '{col}' with mean.")

    # Fill missing categorical
    cat_cols = df.select_dtypes(include=["object"]).columns
    for col in cat_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mode()[0])
            actions.append(f"Filled missing categorical values in '{col}' with mode.")

    # Strip whitespace
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
# COLUMN TOOLS
# -----------------------------
def column_tools(df):
    st.subheader("🧰 Column-Level Cleaning Tools")

    col = st.selectbox("Select a column:", df.columns)

    action = st.radio(
        "Choose an operation:",
        ["Rename column", "Drop column", "Convert to datetime", "Apply custom formula"]
    )

    if action == "Rename column":
        new_name = st.text_input("New column name:")
        if st.button("Rename"):
            df.rename(columns={col: new_name}, inplace=True)
            st.success(f"Column '{col}' renamed to '{new_name}'")

    elif action == "Drop column":
        if st.button("Drop"):
            df.drop(columns=[col], inplace=True)
            st.success(f"Dropped column '{col}'")

    elif action == "Convert to datetime":
        if st.button("Convert"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
            st.success(f"Converted '{col}' to datetime")

    elif action == "Apply custom formula":
        example = st.code("value.lower()", language="python")
        formula = st.text_input("Enter expression using variable 'value':")
        if st.button("Apply"):
            try:
                df[col] = df[col].apply(lambda value: eval(formula))
                st.success("Formula applied successfully!")
            except:
                st.error("Invalid formula.")

    return df


# -----------------------------
# VIEW HISTORY FROM DATABASE
# -----------------------------
def view_history():
    st.title("📁 Cleaning History (Database Stored)")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clean_history ORDER BY id DESC")
    rows = cursor.fetchall()

    if len(rows) == 0:
        st.info("No history available yet.")
        return

    for row in rows:
        id, filename, timestamp, actions_json, rowcount, columns_json, cleaned_csv_text = row

        st.markdown("### ✅ Cleaned File Record")
        st.write(f"**File:** {filename}")
        st.write(f"**Timestamp:** {timestamp}")
        st.write(f"**Rows:** {rowcount}")
        st.write(f"**Columns:** {json.loads(columns_json)}")

        st.write("**Actions:**")
        for action in json.loads(actions_json):
            st.write(f"- {action}")

        # Download cleaned CSV from DB
        st.download_button(
            "Download Cleaned File",
            data=cleaned_csv_text.encode(),
            file_name=f"{filename}_cleaned.csv",
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

st.title("🧼 CSV Data Cleaning Tool (With SQLite Backend)")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Uploaded Data Preview")
    st.dataframe(df.head())
    st.write("---")

    # Auto Clean
    if st.button("⚡ Auto Clean Dataset"):
        cleaned, actions = auto_clean(df.copy())
        st.dataframe(cleaned.head())
        save_to_db(uploaded_file.name, actions, cleaned)
        st.success("Auto-clean complete and saved to database!")

    st.write("---")

    # Data Quality Report
    if st.checkbox("Show Data Quality Report"):
        quality_report(df)

    st.write("---")

    # Column Tools
    st.write("### Advanced Column Tools")
    df = column_tools(df)

    st.write("---")

    # Download cleaned file directly
    csv = df.to_csv(index=False).encode()
    st.download_button(
        "Download Current Cleaned File",
        data=csv,
        file_name="cleaned_output.csv",
        mime="text/csv"
    )
