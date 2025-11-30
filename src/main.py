import streamlit as st
from database import engine, Base
import models

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

st.set_page_config(
    page_title="Cute Docu Shelf",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Cute Docu Shelf")

st.markdown("""
Welcome to **Cute Docu Shelf**!

This application helps you manage document data, import from Excel, and export to Excel.

### Features
- **Dashboard**: View summary of data.
- **Data Entry**: Import data from Excel files.
- **Settings**: Manage configurations.

Use the sidebar to navigate.
""")
