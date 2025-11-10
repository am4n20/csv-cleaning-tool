import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import os
from datetime import datetime

# -----------------------------
# INITIALIZE DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect("outputs.db", check_same_thread=False)
    cursor = conn.cursor()

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
# SAVE CLEANED CSV + METADATA TO DB
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
# AUTO CLEAN FUNCTION
# -----------------------------
def auto_clean(df):
    actions = []

    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        actions.append(f"Removed {before - after} duplicate rows.")

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mean())
            actions.append(f"Filled missing numeric values in '{col}' with mean.")

    cat_cols = df.select_dtypes(include=["object"]).columns
    for col in cat_cols:
        if df[col].isna().sum() > 0:
            df[col] = df[col].fillna(df[col].mode()[0])
            actions.append(f"Filled missing categorical values in '{col}' with mode.")

    for col in cat_cols:
        df[col] = df[col].astype(str).str.strip()

    actions.append("Auto-clean completed.")

    return df, actions

# -----------------------------
# QUALITY REPORT
# -----------------------------
def quality_report(df):
    st.subheader("📊 Data Quality Report")

    st.write("### Missing Values per Column")
    st.bar_chart(df.isna().sum())

    st.write("### Data Types")
    st.dataframe(df.dtypes.to_frame("dtype"))

    st.write("### Duplicate Rows")
    st.write(f"Total duplicates: **{df.duplicated().sum()}**")

    st.write("### Statistics Summary")
    st.dataframe(df.describe(include="all"))

# -----------------------------
# COLUMN LEVEL TOOLS
# -----------------------------
def column_tools(df):
    st.subheader("🧰 Column-Level Cleaning Tools")

    col = st.selectbox("Select a column:", df.columns)

    action = st.radio(
        "Choose an operation:",
        ["Rename column", "Drop column", "Convert to datetime", "Apply custom formula"]
    )

    if action == "Rename column":
        new_name = st.text_input("New name:")
        if st.button("Rename"):
            df.rename(columns={col: new_name}, inplace=True)
            st.success(f"Renamed '{col}' → '{new_name}'")

    elif action == "Drop column":
        if st.button("Drop"):
            df.drop(columns=[col], inplace=True)
            st.success(f"Dropped '{col}'")

    elif action == "Convert to datetime":
        if st.button("Convert"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
            st.success(f"Converted '{col}' to datetime.")

    elif action == "Apply custom formula":
        st.info("Example: value.lower(), value.replace('-', ''), value*2")
        formula = st.text_input("Python expression using variable 'value':")
        if st.button("Apply"):
            try:
                df[col] = df[col].apply(lambda value: eval(formula))
                st.success("Formula applied successfully.")
            except:
                st.error("Invalid formula.")

    return df

# -----------------------------
# CLEANING HISTORY (FROM DB)
# -----------------------------
def view_history():
    st.title("📁 Cleaning History")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clean_history ORDER BY id DESC")
    rows = cursor.fetchall()

    if len(rows) == 0:
        st.info("No cleaning history yet.")
        return

    for row in rows:
        id, filename, timestamp, actions_json, rowcount, columns_json, cleaned_csv_text = row

        st.markdown("### ✅ Cleaned File Record")
        st.write(f"**ID:** {id}")
        st.write(f"**File:** {filename}")
        st.write(f"**Timestamp:** {timestamp}")
        st.write(f"**Rows:** {rowcount}")
        st.write(f"**Columns:** {json.loads(columns_json)}")

        st.write("**Actions Taken:**")
        for action in json.loads(actions_json):
            st.write(f"- {action}")

        st.download_button(
            "⬇️ Download Cleaned File",
            cleaned_csv_text.encode(),
            file_name=f"{filename}_cleaned.csv",
            mime="text/csv",
        )

        st.write("---")

# -----------------------------
# DATABASE VIEWER (NEW PAGE)
# -----------------------------
def database_viewer():
    st.title("🗄️ Database Viewer (Admin Panel)")

    st.write("Database Path:")
    st.code(os.path.abspath("outputs.db"))

    # Download DB
    if os.path.exists("outputs.db"):
        with open("outputs.db", "rb") as db:
            st.download_button("⬇️ Download Database File", db, "outputs.db")

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clean_history")
    rows = cursor.fetchall()

    st.subheader("📌 Table: clean_history")
    if len(rows) == 0:
        st.info("Database is empty.")
        return

    df = pd.DataFrame(rows, columns=[
        "id", "filename", "timestamp", "actions", "rows", "columns", "cleaned_csv"
    ])

    st.dataframe(df)

    st.subheader("🔍 Inspect Cleaned CSV")
    record_id = st.number_input("Enter Record ID", min_value=1, step=1)

    cursor.execute("SELECT cleaned_csv FROM clean_history WHERE id=?", (record_id,))
    result = cursor.fetchone()

    if result:
        cleaned_csv_text = result[0]
        st.code(cleaned_csv_text, language="csv")

        st.download_button(
            "Download This Cleaned CSV",
            cleaned_csv_text.encode(),
            file_name=f"cleaned_record_{record_id}.csv",
            mime="text/csv"
        )
    else:
        st.warning("Record not found.")

# -----------------------------
# MAIN UI
# -----------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Upload & Clean", "Cleaning History", "Database Viewer"])

# Debug info for presenting to sir
st.sidebar.write("Database File Exists:", os.path.exists("outputs.db"))
st.sidebar.write("DB Path:", os.path.abspath("outputs.db"))

if page == "Cleaning History":
    view_history()
    st.stop()

if page == "Database Viewer":
    database_viewer()
    st.stop()

st.title("🧼 CSV Data Cleaning Tool (With SQLite Backend)")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview")
    st.dataframe(df.head())
    st.write("---")

    if st.button("⚡ Auto Clean Dataset"):
        cleaned, actions = auto_clean(df.copy())
        st.dataframe(cleaned.head())
        save_to_db(uploaded_file.name, actions, cleaned)
        st.success("Auto-clean complete & saved to database!")

    st.write("---")

    if st.checkbox("Show Data Quality Report"):
        quality_report(df)

    st.write("---")
    st.write("### Column Tools")
    df = column_tools(df)

    st.write("---")
    st.write("### Download Manually Cleaned File")
    csv = df.to_csv(index=False).encode()
    st.download_button("Download", csv, "cleaned_output.csv", mime="text/csv")
