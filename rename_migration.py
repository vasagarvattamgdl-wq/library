import pandas as pd
import os

DATA_DIR = "data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.xlsx")

def rename_columns():
    if not os.path.exists(BOOKS_FILE):
        print("Books file not found.")
        return

    df = pd.read_excel(BOOKS_FILE)
    
    # Check if old columns exist
    renamed = False
    if 'title_tanglish' in df.columns:
        df = df.rename(columns={'title_tanglish': 'title_thanglish'})
        renamed = True
    if 'author_tanglish' in df.columns:
        df = df.rename(columns={'author_tanglish': 'author_thanglish'})
        renamed = True
        
    if renamed:
        df.to_excel(BOOKS_FILE, index=False)
        print("Successfully renamed columns to 'title_thanglish' and 'author_thanglish'.")
    else:
        print("Columns already renamed or not found.")

if __name__ == "__main__":
    rename_columns()
