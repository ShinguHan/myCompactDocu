import streamlit as st
import pandas as pd
from database import SessionLocal
from services.transaction_service import TransactionService

st.set_page_config(page_title="Data Management", page_icon="📝", layout="wide")

st.title("📝 Data Management")

tab1, tab2 = st.tabs(["Transactions", "Import History"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

with tab1:
    st.header("Transaction Editor")
    
    # Bulk Drop Duplicates
    if st.button("Scan & Drop Duplicates", type="primary"):
        with st.spinner("Scanning for duplicates..."):
            db = SessionLocal()
            service = TransactionService(db)
            try:
                deleted_count = service.delete_duplicates()
                
                if deleted_count > 0:
                    st.success(f"Dropped {deleted_count} duplicate transactions!")
                else:
                    st.info("No duplicates found.")
                        
            except Exception as e:
                st.error(f"Error dropping duplicates: {e}")
            finally:
                db.close()
    
    st.divider()

    # Load Data
    db = SessionLocal()
    service = TransactionService(db)
    df = service.get_all_transactions_df()
    db.close()
    
    if df.empty:
        st.info("No transactions found.")
    else:
        # Data Editor
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "date": st.column_config.DateColumn("Date"),
                "company": st.column_config.TextColumn("Company", disabled=True), # Read-only for V1
                "item": st.column_config.TextColumn("Item", disabled=True),       # Read-only for V1
                "quantity": st.column_config.NumberColumn("Quantity"),
                "unit_price": st.column_config.NumberColumn("Unit Price"),
                "total_amount": st.column_config.NumberColumn("Total Amount"),
                "note": st.column_config.TextColumn("Note"),
            },
            hide_index=True,
            num_rows="dynamic",
            key="data_editor"
        )
        
        # Save Changes Button
        if st.button("Save Changes"):
            try:
                db = SessionLocal()
                service = TransactionService(db)
                progress_bar = st.progress(0)
                total_rows = len(edited_df)
                
                for index, row in edited_df.iterrows():
                    tx_id = row['id']
                    
                    if pd.isna(tx_id):
                        continue 
                        
                    # Update
                    service.update_transaction(tx_id, {
                        "date": row['date'],
                        "quantity": row['quantity'],
                        "unit_price": row['unit_price'],
                        "total_amount": row['total_amount'],
                        "note": row['note']
                    })
                    
                    if index % 100 == 0:
                        progress_bar.progress(min(index / total_rows, 1.0))
                
                db.close()
                progress_bar.empty()
                st.success("Changes saved successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving changes: {e}")

with tab2:
    st.header("Import History")
    
    db = SessionLocal()
    service = TransactionService(db)
    history_df = service.get_import_history_df()
    db.close()
    
    if history_df.empty:
        st.info("No import history found.")
    else:
        st.dataframe(
            history_df,
            column_config={
                "upload_date": st.column_config.DatetimeColumn("Upload Date", format="YYYY-MM-DD HH:mm:ss"),
                "filename": "File Name",
                "success_count": "Imported Count",
                "duplicate_count": "Duplicates Found"
            },
            hide_index=True,
            width='stretch'
        )
