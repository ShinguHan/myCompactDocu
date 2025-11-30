import pandas as pd
from sqlalchemy.orm import Session
from models import Transaction, Company, Item
import io

def export_to_excel(db: Session) -> bytes:
    """
    Exports all transactions to an Excel file in memory.
    Returns the bytes of the Excel file.
    """
    transactions = db.query(Transaction).all()
    
    data = []
    for t in transactions:
        data.append({
            "Date": t.date,
            "Company": t.company.name,
            "Item": t.item.name,
            "Quantity": t.quantity,
            "Unit Price": t.unit_price,
            "Total Amount": t.total_amount,
            "Note": t.note
        })
        
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
        
    return output.getvalue()
