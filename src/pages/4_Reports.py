import streamlit as st
import pandas as pd
import datetime
from database import SessionLocal
from services.report_service import ReportService
from importers.mapping_importer import MappingImporter
from models import ReportMapping

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")

st.title("📈 Reports")

tab1, tab2 = st.tabs(["Monthly Summary", "Mapping Management"])

with tab1:
    st.header("Monthly Summary Report")
    
    col1, col2 = st.columns(2)
    with col1:
        current_year = datetime.date.today().year
        year = st.number_input("Year", min_value=2000, max_value=2100, value=current_year)
    with col2:
        current_month = datetime.date.today().month
        month = st.number_input("Month", min_value=1, max_value=12, value=current_month)
        
    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            db = SessionLocal()
            service = ReportService(db)
            try:
                df = service.generate_monthly_summary(year, month)
                db.close()

                st.subheader("Raw Data")
                st.write(df)
                
                if df.empty:
                    st.info(f"No data found for {year}-{month:02d}.")
                else:
                    st.success(f"Report generated for {year}-{month:02d}")
                    
                    # Split by Category
                    categories = df['Category'].unique()
                    
                    # Sort to ensure consistent order (e.g. 부산물 first if desired, or just sort)
                    categories.sort()
                    
                    for cat in categories:
                        st.subheader(f"{cat}")
                        cat_df = df[df['Category'] == cat].drop(columns=['Category'])
                        st.dataframe(cat_df, width='stretch')
                        
                        # Subtotal for category
                        total_qty = cat_df['Total Quantity'].sum()
                        total_amt = cat_df['Total Amount'].sum()
                        st.markdown(f"**{cat} Total:** Qty: {total_qty:,.1f}, Amount: {total_amt:,.0f} KRW")
                        st.divider()
                    
                    # Export
                    # Simple CSV export for now, or Excel
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 Download CSV (All Data)",
                        data=csv,
                        file_name=f"monthly_report_{year}_{month:02d}.csv",
                        mime="text/csv"
                    )
                    
            except Exception as e:
                st.error(f"Error generating report: {e}")

with tab2:
    st.header("Mapping Management")
    st.markdown("Upload the '폐기물 업체 Mapping' Excel file to update company/item mappings.")
    
    uploaded_file = st.file_uploader("Upload Mapping File", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        if st.button("Update Mappings"):
            with st.spinner("Updating mappings..."):
                try:
                    db = SessionLocal()
                    importer = MappingImporter()
                    
                    data = importer.parse(uploaded_file)
                    count = importer.save(data, db, uploaded_file.name)
                    
                    db.close()
                except Exception as e:
                    st.error(f"Error updating mappings: {e}")

    st.divider()
    st.subheader("Manage Categories")
    st.markdown("Assign categories to items that are missing them.")

    db = SessionLocal()
    # Fetch mappings with missing or Unknown category
    mappings_query = db.query(ReportMapping)
    mappings_df = pd.read_sql(mappings_query.statement, db.bind)
    
    if not mappings_df.empty:
        # Ensure category is string
        mappings_df['category'] = mappings_df['category'].fillna('Unknown')
        
        # Configure column config for data editor
        column_config = {
            "category": st.column_config.SelectboxColumn(
                "Category",
                help="Select the category for this item",
                width="medium",
                options=[
                    "부산물",
                    "폐기물",
                    "Unknown"
                ],
                required=True,
            )
        }
        
        edited_df = st.data_editor(
            mappings_df,
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key="mapping_editor"
        )
        
        if st.button("Save Changes"):
            try:
                # Iterate and update
                count = 0
                for index, row in edited_df.iterrows():
                    # Find original record
                    mapping_id = row['id']
                    new_cat = row['category']
                    
                    # Update in DB
                    record = db.query(ReportMapping).filter(ReportMapping.id == mapping_id).first()
                    if record and record.category != new_cat:
                        record.category = new_cat
                        count += 1
                
                db.commit()
                st.success(f"Successfully updated {count} mappings!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error saving changes: {e}")
    else:
        st.info("No mappings found.")
        
    db.close()

