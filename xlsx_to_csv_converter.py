import pandas as pd
import os

def convert_xlsx_to_csv(xlsx_path):
    try:
        # Read the Excel file
        df = pd.read_excel(xlsx_path)
        
        # Generate output CSV path (same name, different extension)
        csv_path = os.path.splitext(xlsx_path)[0] + '.csv'
        
        # Convert to CSV
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"Successfully converted '{xlsx_path}' to '{csv_path}'")
        return True
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False

if __name__ == "__main__":
    xlsx_path = "/home/yunwei37/北同文化AllForQueer.xlsx"
    convert_xlsx_to_csv(xlsx_path) 