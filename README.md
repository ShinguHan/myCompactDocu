# CompactDocu

**Compact Document Management System for SMEs**

## Overview
CompactDocu is a lightweight, database-driven document management system designed to replace manual Excel workflows. It allows small and medium-sized enterprises to centralize their data, ensuring consistency, security, and ease of access.

## Problem Statement
- **Fragmentation**: Data is scattered across multiple Excel files.
- **Version Control**: Difficult to track the latest version of documents.
- **Searchability**: Finding specific records across multiple sheets is time-consuming.

## Solution
A Streamlit-based web application backed by a SQLite database. This system provides a user-friendly interface for:
- Uploading and parsing Excel files.
- Storing data in a structured database.
- Searching, filtering, and managing records.

## Key Features
- **Excel Import**: Drag-and-drop interface to upload Excel files and automatically save them to the database.
- **Centralized Database**: Uses SQLite for a portable yet robust data storage solution.
- **Data Management**: View, edit, and delete records via a web interface.
- **Search**: Powerful filtering capabilities to find information instantly.

## Getting Started

### Prerequisites
- Python 3.8 or higher

### Installation
1. Clone the repository or download the source code.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
```bash
streamlit run app.py
```