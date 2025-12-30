import pandas as pd
import os
from transliterate_utils import transliterate_text

DATA_DIR = "data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.xlsx")

def is_tamil(text):
    if not isinstance(text, str): return False
    for char in text:
        if '\u0B80' <= char <= '\u0BFF':
            return True
    return False

def run_migration():
    if not os.path.exists(BOOKS_FILE):
        print("Books file not found.")
        return

    df = pd.read_excel(BOOKS_FILE)
    
    count = 0
    for index, row in df.iterrows():
        title = row.get('title', '')
        author = row.get('author', '')
        
        # Transliterate Title if needed
        t_tang = row.get('title_thanglish', '')
        if is_tamil(title) and (pd.isna(t_tang) or str(t_tang).strip() == ""):
            new_val = transliterate_text(title)
            df.at[index, 'title_thanglish'] = new_val
            count += 1
            
        # Transliterate Author if needed
        a_tang = row.get('author_thanglish', '')
        if is_tamil(author) and (pd.isna(a_tang) or str(a_tang).strip() == ""):
            new_val = transliterate_text(author)
            df.at[index, 'author_thanglish'] = new_val
            count += 1
            
    if count > 0:
        df.to_excel(BOOKS_FILE, index=False)
        print(f"Successfully processed {count} fields.")
    else:
        print("No new Tamil fields found to transliterate.")

if __name__ == "__main__":
    run_migration()
