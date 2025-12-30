import pandas as pd
import os
from datetime import datetime

# Input file
SOURCE_FILE = "source/master.xlsx"

# Output files
DATA_DIR = "data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.xlsx")
USERS_FILE = os.path.join(DATA_DIR, "users.xlsx")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.xlsx")

def generate_id(prefix, number, width=3):
    return f"{prefix}-{str(number).zfill(width)}"

def migrate():
    print("Starting migration...")
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    try:
        # Load source data
        df = pd.read_excel(SOURCE_FILE)
    except FileNotFoundError:
        print(f"Error: Source file '{SOURCE_FILE}' not found.")
        return

    # Normalize column names
    df.columns = df.columns.str.strip()
    
    # --- 1. Create Users Database ---
    print("Processing users...")
    legacy_users_raw = df['With Whom'].dropna().unique()
    legacy_users = [str(u).strip() for u in legacy_users_raw if str(u).strip() != '']
    
    users_data = []
    # Admin
    users_data.append({
        'user_id': format(generate_id('MEM', 1)),
        'name': 'Admin',
        'email': 'admin@library.com',
        'mobile': '',
        'role': 'ADMIN'
    })
    
    # Legacy Users
    user_map = {} # Name -> User ID
    current_user_id = 2
    for name in legacy_users:
        u_id = generate_id('MEM', current_user_id)
        users_data.append({
            'user_id': u_id,
            'name': name,
            'email': '', # Legacy users have no email initially
            'mobile': '',
            'role': 'USER'
        })
        user_map[name] = u_id
        current_user_id += 1
    
    users_df = pd.DataFrame(users_data)
    users_df.to_excel(USERS_FILE, index=False)
    print(f"Created {USERS_FILE} with {len(users_df)} users.")

    # --- 2. Create Books & Transactions ---
    print("Processing books and transactions...")
    
    books_data = []
    transactions_data = []
    
    book_counter = 1
    tx_counter = 1
    
    for index, row in df.iterrows():
        book_id = generate_id('GDL', book_counter)
        title = str(row['Book Name']).strip() if pd.notna(row['Book Name']) else "Unknown Title"
        author = str(row['Author']).strip() if pd.notna(row['Author']) else "Unknown Author"
        donated_by = str(row['Donated By']).strip() if pd.notna(row['Donated By']) else ""
        
        # Status Check
        availability_raw = str(row['Avalibility']).strip().upper()
        
        if availability_raw == 'NO':
            status = 'BORROWED'
            borrower_name = str(row['With Whom']).strip() if pd.notna(row['With Whom']) else None
            
            if borrower_name and borrower_name in user_map:
                u_id = user_map[borrower_name]
                # Find user details from our list
                # (For optimization, we just use the map and what we know)
                
                transactions_data.append({
                    'transaction_id': generate_id('TX', tx_counter, width=5),
                    'book_id': book_id,
                    'book_title': title,
                    'user_id': u_id,
                    'user_name': borrower_name,
                    'user_email': '',
                    'user_mobile': '',
                    'borrow_date': datetime.now().strftime("%Y-%m-%d"),
                    'return_date': None,
                    'status': 'ACTIVE' # Active Loan
                })
                tx_counter += 1
        else:
            status = 'AVAILABLE'
            
        books_data.append({
            'id': book_id,
            'title': title,
            'author': author,
            'donated_by': donated_by,
            'status': status
        })
        book_counter += 1

    books_df = pd.DataFrame(books_data)
    books_df.to_excel(BOOKS_FILE, index=False)
    print(f"Created {BOOKS_FILE} with {len(books_df)} books.")

    # Transactions Structure
    if not transactions_data:
        transactions_df = pd.DataFrame(columns=[
            'transaction_id', 'book_id', 'book_title', 'user_id', 
            'user_name', 'user_email', 'user_mobile', 
            'borrow_date', 'return_date', 'status'
        ])
    else:
        transactions_df = pd.DataFrame(transactions_data)
        
    transactions_df.to_excel(TRANSACTIONS_FILE, index=False)
    print(f"Created {TRANSACTIONS_FILE} with {len(transactions_df)} transactions.")
    
    print("Migration execution successful.")

if __name__ == "__main__":
    migrate()
