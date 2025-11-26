import streamlit as st
import pandas as pd
from src import database, utils

# Page Config
st.set_page_config(
    page_title="CompactDocu",
    page_icon="📂",
    layout="wide"
)

# Initialize DB
if 'db_initialized' not in st.session_state:
    database.init_db()
    st.session_state['db_initialized'] = True

def main():
    st.title("📂 CompactDocu")
    st.subheader("SME Document Management System")

    # Sidebar Navigation
    menu = ["Upload", "Search & View", "Manage"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Upload":
        st.header("Upload Excel File")
        
        upload_type = st.radio("Select File Type", ["Disposal/Waste Records", "Gate Pass Records"])
        uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            st.info("File uploaded successfully! Parsing...")
            
            if upload_type == "Disposal/Waste Records":
                df = utils.parse_disposal_file(uploaded_file)
                table_name = 'disposal_records'
                if df is None or df.empty:
                    st.warning("Failed to parse as Disposal Records. Trying Gate Pass format...")
                    df = utils.parse_gate_pass_file(uploaded_file)
                    if df is not None and not df.empty:
                        table_name = 'gate_pass_records'
                        st.success("Successfully parsed as Gate Pass Records!")

            else: # Gate Pass Records
                df = utils.parse_gate_pass_file(uploaded_file)
                table_name = 'gate_pass_records'
                if df is None or df.empty:
                    st.warning("Failed to parse as Gate Pass Records. Trying Disposal format...")
                    df = utils.parse_disposal_file(uploaded_file)
                    if df is not None and not df.empty:
                        table_name = 'disposal_records'
                        st.success("Successfully parsed as Disposal Records!")
            
            if df is not None and not df.empty:
                st.write("### Preview")
                st.dataframe(df.head())
                st.write(f"Total Rows: {len(df)}")
                st.write(f"Target Table: `{table_name}`")
                
                if st.button("Save to Database"):
                    try:
                        database.save_dataframe(df, table_name)
                        st.success(f"Successfully saved {len(df)} records to '{table_name}'")
                    except Exception as e:
                        st.error(f"Error saving to database: {e}")
            else:
                st.error("Could not parse the Excel file. Please check the format.")

    elif choice == "Search & View":
        st.header("Search Database")
        
        view_type = st.radio("Select Data to View", ["Disposal/Waste Records", "Gate Pass Records"])
        table_name = 'disposal_records' if view_type == "Disposal/Waste Records" else 'gate_pass_records'
        
        if st.button("Load Data"):
            try:
                df = database.load_data(table_name)
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error loading data: {e}")

    elif choice == "Manage":
        st.header("Manage System")
        st.write("Database Path:", database.DB_PATH)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Re-initialize Database"):
                database.init_db()
                st.success("Database re-initialized.")
        
        with col2:
            if st.button("Clear All Data (Danger!)"):
                database.clear_table('disposal_records')
                database.clear_table('gate_pass_records')
                st.warning("All data cleared.")

if __name__ == '__main__':
    main()
