import streamlit as st
import pandas as pd
import datetime
import os
from database import SessionLocal
from services.report_service import ReportService
from models import ReportMapping
from services.print_service import PrintService

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")

st.title("📈 Reports")

# Base paths (relative to this file's location)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_PATH = os.path.join(BASE_DIR, "ref", "반출증_Template.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

tab1, tab2, tab3 = st.tabs(["Monthly Summary", "Mapping Management", "Transaction History"])

# ─────────────────────────────────────────────
# Tab 1: Monthly Summary
# ─────────────────────────────────────────────
with tab1:
    st.header("Monthly Summary Report")

    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("Year", min_value=2000, max_value=2100, value=datetime.date.today().year)
    with col2:
        month = st.number_input("Month", min_value=1, max_value=12, value=datetime.date.today().month)

    if st.button("Generate Report", type="primary"):
        with st.spinner("Generating report..."):
            db = SessionLocal()
            service = ReportService(db)
            try:
                df = service.generate_monthly_summary(year, month)
                st.success(f"Report generated for {year}-{month:02d}")
            except Exception as e:
                st.error(f"Error generating report: {e}")
                df = pd.DataFrame()
            finally:
                db.close()

            if not df.empty:
                by_products = df[df['Category'] == '부산물'].drop(columns=['Category'])
                waste = df[df['Category'] == '폐기물'].drop(columns=['Category'])

                column_config = {
                    "Unit Price": st.column_config.NumberColumn("단가", format="%d"),
                    "Current Qty": st.column_config.NumberColumn("당월 계근량", format="%d"),
                    "Current Amount": st.column_config.NumberColumn("당월 매각금액", format="%d"),
                    "Previous Amount": st.column_config.NumberColumn("전월 매각금액", format="%d"),
                    "Company": st.column_config.TextColumn("업체명"),
                    "Item": st.column_config.TextColumn("품명"),
                    "Note": st.column_config.TextColumn("비고"),
                }
                col_order = ["Company", "Item", "Unit Price", "Current Qty", "Current Amount", "Previous Amount", "Note"]

                st.subheader("1. 부산물 매각현황")
                if not by_products.empty:
                    st.dataframe(by_products, use_container_width=True, hide_index=True,
                                 column_config=column_config, column_order=col_order)
                    st.markdown(f"**합계**: 당월 수량 `{by_products['Current Qty'].sum():,.0f}`, "
                                f"당월 금액 `{by_products['Current Amount'].sum():,.0f}`, "
                                f"전월 금액 `{by_products['Previous Amount'].sum():,.0f}`")
                else:
                    st.info("이번 달 부산물 데이터가 없습니다.")

                st.divider()

                st.subheader("2. 폐기물 처리현황")
                if not waste.empty:
                    st.dataframe(waste, use_container_width=True, hide_index=True,
                                 column_config=column_config, column_order=col_order)
                    st.markdown(f"**합계**: 당월 수량 `{waste['Current Qty'].sum():,.0f}`, "
                                f"당월 금액 `{waste['Current Amount'].sum():,.0f}`, "
                                f"전월 금액 `{waste['Previous Amount'].sum():,.0f}`")
                else:
                    st.info("이번 달 폐기물 데이터가 없습니다.")
            else:
                st.info(f"{year}-{month:02d} 데이터가 없습니다.")

# ─────────────────────────────────────────────
# Tab 2: Mapping Management
# ─────────────────────────────────────────────
with tab2:
    st.header("Mapping Management")
    st.markdown("품목/업체에 카테고리(부산물/폐기물)를 지정합니다.")

    db = SessionLocal()
    service = ReportService(db)
    new_count = service.sync_mappings()
    if new_count > 0:
        st.toast(f"새 항목 {new_count}개 발견. 카테고리를 지정해주세요.")

    mappings_query = db.query(ReportMapping)
    with db.get_bind().connect() as conn:
        mappings_df = pd.read_sql(mappings_query.statement, conn)

    if not mappings_df.empty:
        mappings_df['category'] = mappings_df['category'].fillna('Unknown')

        column_config = {
            "category": st.column_config.SelectboxColumn(
                "Category",
                width="medium",
                options=["부산물", "폐기물", "Unknown"],
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
                count = 0
                for _, row in edited_df.iterrows():
                    record = db.query(ReportMapping).filter(ReportMapping.id == row['id']).first()
                    if record and record.category != row['category']:
                        record.category = row['category']
                        count += 1
                db.commit()
                st.success(f"{count}개 항목이 업데이트되었습니다.")
                st.rerun()
            except Exception as e:
                st.error(f"저장 오류: {e}")
    else:
        st.info("매핑 데이터가 없습니다.")

    db.close()

# ─────────────────────────────────────────────
# Tab 3: Transaction History & Exit Pass
# ─────────────────────────────────────────────
with tab3:
    st.header("Transaction History & Exit Pass")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=7))
    with col2:
        end_date = st.date_input("End Date", value=datetime.date.today())

    if st.button("Search Transactions"):
        db = SessionLocal()
        service = ReportService(db)
        transactions = service.get_grouped_transactions(start_date, end_date)
        db.close()

        if not transactions:
            st.info("해당 기간에 거래 내역이 없습니다.")
        else:
            st.success(f"{len(transactions)}개 그룹 조회됨.")

            for i, tx in enumerate(transactions):
                with st.expander(f"{tx['date']} - {tx['company_name']} ({len(tx['items'])}개 품목)"):
                    st.table(pd.DataFrame(tx['items']))

                    print_service = PrintService(TEMPLATE_PATH)
                    output_filename = f"exit_pass_{tx['date']}_{tx['company_name']}.xlsx".replace(" ", "_").replace(":", "-")
                    output_path = os.path.join(OUTPUT_DIR, output_filename)
                    os.makedirs(OUTPUT_DIR, exist_ok=True)

                    try:
                        print_service.generate_exit_pass(tx, output_path)
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="반출증 다운로드 (Excel)",
                                data=f,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_{i}"
                            )
                    except Exception as e:
                        st.error(f"반출증 생성 오류: {e}")
