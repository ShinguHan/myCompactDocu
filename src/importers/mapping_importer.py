import pandas as pd
from sqlalchemy.orm import Session
from models import ReportMapping
from .base import BaseImporter

class MappingImporter(BaseImporter):
    def parse(self, file_input) -> list:
        """
        Parses the Mapping Excel file.
        Expected columns: '품명', '업체명', '연간처리 품명', '연간처리 업체'
        """
        xls = pd.ExcelFile(file_input)
        
        # Check for '폐기물 업체 Mapping' sheet, or just use the first one if not found?
        # User mentioned '폐기물 업체 Mapping' sheet.
        sheet_name = '폐기물 업체 Mapping'
        if sheet_name not in xls.sheet_names:
            # Fallback to first sheet if specific name not found, or raise error?
            # Let's try to find it, if not, use first sheet but warn.
            if len(xls.sheet_names) > 0:
                sheet_name = xls.sheet_names[0]
            else:
                raise ValueError("No sheets found in file.")
        
        df = pd.read_excel(xls, sheet_name=sheet_name)
        
        # Normalize columns
        df.columns = [str(c).strip() for c in df.columns]
        
        required_cols = ['품명', '업체명', '연간처리 품명', '연간처리 업체', '구분']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        mappings = []
        for _, row in df.iterrows():
            mappings.append({
                'raw_item': str(row['품명']).strip(),
                'raw_company': str(row['업체명']).strip(),
                'standard_item': str(row['연간처리 품명']).strip(),
                'standard_company': str(row['연간처리 업체']).strip(),
                'category': str(row['구분']).strip()
            })
            
        return mappings

    def validate(self, data: list) -> list:
        return data

    def save(self, data: list, db: Session, filename: str) -> int:
        """
        Saves mappings. Replaces existing mapping if (raw_item, raw_company) exists.
        """
        count = 0
        for m in data:
            # Check if exists
            existing = db.query(ReportMapping).filter(
                ReportMapping.raw_item == m['raw_item'],
                ReportMapping.raw_company == m['raw_company']
            ).first()
            
            if existing:
                existing.standard_item = m['standard_item']
                existing.standard_company = m['standard_company']
                existing.category = m['category']
            else:
                new_mapping = ReportMapping(
                    raw_item=m['raw_item'],
                    raw_company=m['raw_company'],
                    standard_item=m['standard_item'],
                    standard_company=m['standard_company'],
                    category=m['category']
                )
                db.add(new_mapping)
            count += 1
            
        db.commit()
        return count
