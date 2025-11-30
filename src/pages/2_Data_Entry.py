import streamlit as st
import pandas as pd
from database import SessionLocal
from importers.waste_importer import WasteImporter
from services.transaction_service import TransactionService
from services.analytics_service import AnalyticsService

st.set_page_config(page_title="Data Entry", page_icon="📥")

st.title("📥 Data Entry")

tab1, tab2 = st.tabs(["Import from Excel", "Manual Entry"])

with tab1:
    st.markdown("### Import Excel File")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        if st.button("Analyze & Import"):
            with st.spinner("Analyzing file..."):
                try:
                    importer = WasteImporter()
                    
                    # 1. Parse Data
                    parsed_data = importer.parse(uploaded_file)
                    st.info(f"Parsed {len(parsed_data)} transactions from file.")
                    
                    # 2. Check Duplicates
                    db = SessionLocal()
                    check_result = importer.check_duplicates(parsed_data, db)
                    db.close()
                    
                    new_count = len(check_result['new'])
                    dup_count = len(check_result['duplicates'])
                    
                    st.write(f"**Analysis Result:**")
                    st.write(f"- New Transactions: {new_count}")
                    st.write(f"- Duplicate Transactions: {dup_count}")
                    
                    if dup_count > 0:
                        st.warning("Duplicates found! These transactions already exist in the database (same Date, Company, and Item).")
                        st.markdown("##### Duplicate Details")
                        st.dataframe(pd.DataFrame(check_result['duplicates']))
                    
                    # Store results in session state to persist across reruns
                    st.session_state['parsed_data'] = parsed_data
                    st.session_state['check_result'] = check_result
                    st.session_state['analysis_done'] = True
                    
                except Exception as e:
                    st.error(f"Error analyzing file: {e}")

    if st.session_state.get('analysis_done'):
        st.divider()
        st.markdown("### Confirm Import")
        
        check_result = st.session_state['check_result']
        parsed_data = st.session_state['parsed_data']
        
        import_option = st.radio(
            "How to handle duplicates?",
            ("Skip Duplicates", "Import All (Allow Duplicates)"),
            index=0
        )
        
        if st.button("Confirm Import"):
            try:
                to_import = []
                if import_option == "Skip Duplicates":
                    to_import = check_result['new']
                else:
                    to_import = parsed_data
                
                if not to_import:
                    st.warning("No transactions to import.")
                else:
                    db = SessionLocal()
                    importer = WasteImporter()
                    
                    # Calculate duplicate count based on user choice
                    dup_count_for_history = len(check_result['duplicates'])
                    
                    count = importer.save(to_import, db, uploaded_file.name, dup_count_for_history)
                    db.close()
                    st.success(f"Successfully imported {count} transactions!")
                    
                    # Clear session state
                    del st.session_state['parsed_data']
                    del st.session_state['check_result']
                    del st.session_state['analysis_done']
                    
            except Exception as e:
                st.error(f"Error saving data: {e}")

with tab2:
    st.markdown("### Manual Transaction Entry (Batch)")
    
    # Initialize session state for batch entry
    if 'batch_items' not in st.session_state:
        st.session_state['batch_items'] = []
    
    db = SessionLocal()
    analytics_service = AnalyticsService(db)
    # We need full objects to get IDs for contract lookup
    companies = analytics_service.get_companies()
    items = analytics_service.get_items()
    
    # Map names to IDs for easy lookup
    company_map = {c.name: c.id for c in companies}
    item_map = {i.name: i.id for i in items}
    
    from services.contract_service import ContractService
    contract_service = ContractService(db)
    
    # --- Master Section ---
    st.markdown("#### 1. Select Date & Company")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        date = st.date_input("Date", key="batch_date")
    with col_m2:
        company_name = st.selectbox("Company", [""] + list(company_map.keys()), key="batch_company")

    st.divider()
    
    # --- Detail Section ---
    st.markdown("#### 2. Add Items")
    
    if not company_name:
        st.info("Please select a Company first.")
    else:
        with st.form("add_item_form", clear_on_submit=True):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                item_name = st.selectbox("Item", [""] + list(item_map.keys()))
            with col_d2:
                # If new item, we can't lookup contract easily yet. 
                # For V1 batch, let's assume existing items or simple add.
                # If user wants new item, they might need to go to a "Manage Items" page or we add "Create New" here too?
                # "Create New" in batch is complex. Let's stick to existing items for Contract logic first.
                pass
            
            # Contract Lookup
            suggested_price = 0.0
            is_fixed_total = False
            fixed_total_val = 0.0
            
            if item_name and company_name:
                cid = company_map.get(company_name)
                iid = item_map.get(item_name)
                if cid and iid:
                    contract = contract_service.get_contract(cid, iid, date)
                    if contract:
                        if contract.fixed_total_amount is not None:
                            is_fixed_total = True
                            fixed_total_val = contract.fixed_total_amount
                        if contract.unit_price is not None:
                            suggested_price = contract.unit_price
            
            col_d3, col_d4, col_d5 = st.columns(3)
            with col_d3:
                quantity = st.number_input("Quantity", min_value=0.0, step=0.1)
            with col_d4:
                unit_price = st.number_input("Unit Price", value=suggested_price, min_value=0.0, step=10.0)
            with col_d5:
                # Auto-calc logic
                # Streamlit forms don't update interactively. 
                # We can't show the calc result *before* submit in a form easily.
                # But we can calculate it *on submit*.
                # User can override if they want? 
                # Let's ask for Total Amount but hint it will be auto-calced if 0.
                total_amount_input = st.number_input("Total Amount (Leave 0 for Auto-Calc)", min_value=0.0, step=100.0)

            add_submitted = st.form_submit_button("Add to List")
            
            if add_submitted:
                if not item_name:
                    st.error("Item is required.")
                else:
                    # Calculate Total
                    final_total = total_amount_input
                    if final_total == 0:
                        if is_fixed_total:
                            final_total = fixed_total_val
                        else:
                            final_total = quantity * unit_price
                    
                    st.session_state['batch_items'].append({
                        "item_name": item_name,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_amount": final_total,
                        "note": "" # Optional note for batch?
                    })
                    st.rerun()

    # --- List Section ---
    if st.session_state['batch_items']:
        st.markdown("#### 3. Review & Save")
        
        # Show list
        batch_df = pd.DataFrame(st.session_state['batch_items'])
        st.dataframe(batch_df, width='stretch')
        
        # Remove item option
        if st.button("Clear List"):
            st.session_state['batch_items'] = []
            st.rerun()
            
        if st.button("Save All Transactions", type="primary"):
            try:
                service = TransactionService(db)
                saved_count = 0
                for item in st.session_state['batch_items']:
                    data = {
                        "date": date,
                        "company_name": company_name,
                        "item_name": item['item_name'],
                        "quantity": item['quantity'],
                        "unit_price": item['unit_price'],
                        "total_amount": item['total_amount'],
                        "note": item.get('note', '')
                    }
                    service.create_transaction(data)
                    saved_count += 1
                
                st.success(f"Successfully saved {saved_count} transactions!")
                st.session_state['batch_items'] = []
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving transactions: {e}")
    
    db.close()
