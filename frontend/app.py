import streamlit as st
import requests
import pandas as pd
import os

# ===============================
# CONFIG
# ===============================
API = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="CSV Data Cleaning Tool", 
    layout="wide",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.title("🧹 CSV Data Cleaning Tool")

# Sidebar Navigation
page = st.sidebar.radio("Go to", ["Upload & Clean", "Cleaning History"])

# ===============================
# HELPER FUNCTIONS (CACHED)
# ===============================
@st.cache_data(ttl=5)
def fetch_history():
    try:
        response = requests.get(f"{API}/history", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []

# ===============================
# SIDEBAR - GLOBAL DOWNLOAD
# ===============================
st.sidebar.markdown("---")
st.sidebar.subheader("Global Actions")

# Fetch history for sidebar download
hist_data = fetch_history()
if hist_data:
    try:
        df_hist_global = pd.DataFrame(hist_data)
        
        # Format 'actions' list to string if it exists
        if "actions_taken" in df_hist_global.columns:
            df_hist_global["actions_taken"] = df_hist_global["actions_taken"].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
        
        # Timestamp cleanup
        if "timestamp" in df_hist_global.columns:
            df_hist_global["timestamp"] = df_hist_global["timestamp"].astype(str)

        csv_global = df_hist_global.to_csv(index=False).encode('utf-8')
        
        st.sidebar.download_button(
            label="📄 Download History (CSV)",
            data=csv_global,
            file_name="full_cleaning_history.csv",
            mime="text/csv",
            help="Download the entire cleaning history as a CSV file."
        )
    except Exception:
        pass

# ===============================
# UPLOAD & CLEAN PAGE
# ===============================
if page == "Upload & Clean":

    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

    if uploaded_file:
        # ---- Upload file to backend ----
        # Using session state to avoid re-uploading on every interaction
        if "file_id" not in st.session_state or st.session_state.get("uploaded_file_name") != uploaded_file.name:
            with st.spinner("Uploading..."):
                upload_response = requests.post(f"{API}/upload", files={"file": uploaded_file})
                
                if upload_response.status_code == 200:
                    upload_data = upload_response.json()
                    st.session_state["file_id"] = upload_data["file_id"]
                    st.session_state["columns"] = upload_data["columns"]
                    st.session_state["preview"] = upload_data["preview"]
                    st.session_state["uploaded_file_name"] = uploaded_file.name
                    st.success("File uploaded successfully!")
                else:
                    st.error(f"Upload failed: {upload_response.text}")
                    st.stop()
        
        # Use simple variables for easier access
        file_id = st.session_state.get("file_id")
        current_columns = st.session_state.get("columns", [])

        # ===============================
        # STEP 1: RENAME COLUMNS
        # ===============================
        st.subheader("1. Rename Columns (Optional)")
        
        with st.expander("Click to rename columns"):
            # New UI: Select Column -> Input New Name -> Apply
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                selected_col = st.selectbox("Select Column to Rename", current_columns)
            
            with col2:
                new_col_name = st.text_input("Enter New Name", placeholder=selected_col)
            
            with col3:
                st.write("") # Spacer
                st.write("") # Spacer
                if st.button("Rename"):
                    if new_col_name and new_col_name != selected_col:
                        with st.spinner("Renaming..."):
                            rename_response = requests.post(
                                f"{API}/rename",
                                json={"file_id": file_id, "columns": {selected_col: new_col_name}}
                            )
                            if rename_response.status_code == 200:
                                st.success(f"Renamed '{selected_col}' to '{new_col_name}'")
                                # Update Session State
                                new_data = rename_response.json()
                                st.session_state["columns"] = new_data["columns"]
                                st.session_state["preview"] = new_data["preview"]
                                st.rerun() # Use st.rerun() instead of experimental_rerun
                            else:
                                st.error("Failed to rename columns")
                    else:
                        st.warning("Please enter a valid new name.")

        st.subheader("Preview")
        if "preview" in st.session_state:
            st.dataframe(st.session_state["preview"])

        # ===============================
        # STEP 2: AUTO CLEAN
        # ===============================
        st.subheader("2. Clean Data")
        if st.button("⚡ Auto Clean Dataset"):
            with st.spinner("Cleaning..."):
                response = requests.post(
                    f"{API}/auto-clean",
                    params={"file_id": file_id}
                )

                if response.status_code == 200:
                    clean_data = response.json()
                    st.success("Auto-clean completed successfully!")

                    # ---- Downloads ----
                    download_url = f"{API}/files/cleaned/{file_id}"
                    st.markdown(f"### [⬇️ Download Cleaned CSV]({download_url})")

                    # ---- Report ----
                    st.subheader("Data Quality Report")
                    
                    report = clean_data["report"]
                    
                    # Visuals - Missing Data
                    st.write("#### Missing Values")
                    if report["missing"]:
                        missing_df = pd.DataFrame(list(report["missing"].items()), columns=["Column", "Missing Count"])
                        st.dataframe(missing_df, width=1000)
                        
                        if missing_df["Missing Count"].sum() > 0:
                            st.bar_chart(missing_df.set_index("Column"))
                    else:
                        st.info("No missing values found.")

                    # Visuals - Stats
                    if "stats" in report and report["stats"]:
                        st.write("#### Statistical Summary")
                        st.dataframe(pd.DataFrame(report["stats"]))

                    st.subheader("Actions Taken")
                    if clean_data["actions"]:
                        st.write(clean_data["actions"])
                    else:
                        st.write("No actions needed.")

                else:
                    st.error("Auto-clean failed")
                    st.text(response.text)

# ===============================
# CLEANING HISTORY PAGE
# ===============================
elif page == "Cleaning History":

    try:
        response = requests.get(f"{API}/history", timeout=5)
        if response.status_code == 200:
            history = response.json()
            
            if not history:
                st.info("No cleaning history available yet.")
            else:
                st.subheader("Cleaning History")
                
                # Convert to DataFrame
                df_history = pd.DataFrame(history)
                if "timestamp" in df_history.columns:
                    df_history["timestamp"] = df_history["timestamp"].astype(str)
                
                # Download Button for Report
                csv_history = df_history.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Download History Report (CSV)",
                    data=csv_history,
                    file_name="cleaning_history_report.csv",
                    mime="text/csv"
                )

                # Display Records
                for record in history:
                    ts = record.get('timestamp', 'Unknown Time')
                    fname = record.get('filename', 'Unknown File')
                    with st.expander(f"{fname} - {ts}"):
                        st.write(f"**Rows:** {record.get('rows')}")
                        st.write(f"**Columns:** {record.get('columns')}")
                        st.write(f"**Actions Taken:** {record.get('actions_taken')}")
        else:
            st.error("Failed to fetch history from backend.")
            
    except Exception as e:
        st.error(f"Count not connect to backend: {e}")
