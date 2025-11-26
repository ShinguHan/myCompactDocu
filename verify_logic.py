import os
import sys
import pandas as pd
from src import database, utils

# Add current directory to path
sys.path.append(os.getcwd())

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
DISPOSAL_FILE = os.path.join(REF_DIR, '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx')
GATE_PASS_FILE = os.path.join(REF_DIR, '반출증_2025011 새버젼.xlsx')

def verify():
    print("--- Starting Verification ---")
    
    # 1. Init DB
    print("Initializing Database...")
    # Cannot remove file if locked by Streamlit. Drop tables instead.
    from sqlalchemy import text
    with database.ENGINE.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS disposal_records"))
        conn.execute(text("DROP TABLE IF EXISTS gate_pass_records"))
        conn.commit()
        
    database.init_db()
    
    # Clear existing data for clean test (redundant if file removed, but safe)
    # database.clear_table('disposal_records')
    # database.clear_table('gate_pass_records')
    
    # 2. Test Disposal Parsing
    print(f"\nParsing Disposal File")
    if os.path.exists(DISPOSAL_FILE):
        try:
            df_disposal = utils.parse_disposal_file(DISPOSAL_FILE)
            if df_disposal is not None and not df_disposal.empty:
                print(f"  Success! Parsed {len(df_disposal)} rows.")
                
                # Save to DB
                database.save_dataframe(df_disposal, 'disposal_records')
                print("  Saved to DB.")
            else:
                print("  Failed to parse disposal file (empty or None).")
        except Exception as e:
            print(f"  Error parsing disposal file: {e}")
    else:
        print("  File not found.")

    # 3. Test Gate Pass Parsing
    print(f"\nParsing Gate Pass File")
    if os.path.exists(GATE_PASS_FILE):
        # Try parsing as Gate Pass
        try:
            df_gate = utils.parse_gate_pass_file(GATE_PASS_FILE)
            if df_gate is not None and not df_gate.empty:
                print(f"  Success (as Gate Pass)! Parsed {len(df_gate)} rows.")
                database.save_dataframe(df_gate, 'gate_pass_records')
            else:
                print("  Failed to parse as Gate Pass.")
                
                # Try parsing as Disposal (since it might contain disposal data)
                print("  Attempting to parse as Disposal Records...")
                df_disposal_2 = utils.parse_disposal_file(GATE_PASS_FILE)
                if df_disposal_2 is not None and not df_disposal_2.empty:
                    print(f"  Success (as Disposal)! Parsed {len(df_disposal_2)} rows.")
                    database.save_dataframe(df_disposal_2, 'disposal_records')
                else:
                    print("  Failed to parse as Disposal too.")
        except Exception as e:
            print(f"  Error parsing gate pass file: {e}")
    else:
        print("  File not found.")

    # 4. Verify DB Content
    print("\n--- Verifying Database Content ---")
    df_d = database.load_data('disposal_records')
    print(f"Disposal Records in DB: {len(df_d)}")
    
    df_g = database.load_data('gate_pass_records')
    print(f"Gate Pass Records in DB: {len(df_g)}")

if __name__ == "__main__":
    verify()
