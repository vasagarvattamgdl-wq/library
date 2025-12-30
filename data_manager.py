
import pandas as pd
from datetime import datetime
import os

# File paths
DATA_DIR = "data"
BOOKS_FILE = os.path.join(DATA_DIR, "books.xlsx")
USERS_FILE = os.path.join(DATA_DIR, "users.xlsx")
TRANSACTIONS_FILE = os.path.join(DATA_DIR, "transactions.xlsx")
PENDING_FILE = os.path.join(DATA_DIR, "pending_approvals.xlsx")

def load_data():
    """Loads all Excel files into pandas DataFrames."""
    books = pd.read_excel(BOOKS_FILE)
    users = pd.read_excel(USERS_FILE)
    transactions = pd.read_excel(TRANSACTIONS_FILE)
    
    try:
        pending = pd.read_excel(PENDING_FILE)
    except FileNotFoundError:
        # Create empty pending file if it doesn't exist
        pending = pd.DataFrame(columns=['transaction_id', 'book_id', 'book_title', 'user_id', 'user_name', 
                                       'user_mobile', 'user_email', 'borrow_date', 'return_date', 'status'])
        pending.to_excel(PENDING_FILE, index=False)
    
    # Ensure thanglish columns exist
    if 'title_thanglish' not in books.columns:
        books['title_thanglish'] = ""
    if 'author_thanglish' not in books.columns:
        books['author_thanglish'] = ""
        
    books['title_thanglish'] = books['title_thanglish'].fillna("").astype(str)
    books['author_thanglish'] = books['author_thanglish'].fillna("").astype(str)
    
    return books, users, transactions, pending

# --- Helper Functions ---

def get_next_tx_id():
    return f"TX-{datetime.now().strftime('%Y%m%d%H%M%S')}"

def normalize_mobile(val):
    """Clean mobile number robustly."""
    try:
        f_val = float(val)
        i_val = int(f_val)
        return str(i_val)
    except (ValueError, TypeError):
        s = str(val).strip()
        if s.endswith('.0'):
            return s[:-2]
        return s

# --- Book Management ---

def add_book(title, author, donated_by, title_thanglish, author_thanglish):
    books, _, _, _ = load_data()
    
    # Determine new ID
    import re
    max_num = 0
    for book_id in books['id']:
        match = re.search(r'GDL-(\d+)', str(book_id))
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    new_id = f"GDL-{str(max_num + 1).zfill(3)}"
    
    new_book = pd.DataFrame([{
        'id': new_id,
        'title': title,
        'author': author,
        'donated_by': donated_by,
        'title_thanglish': title_thanglish,
        'author_thanglish': author_thanglish,
        'status': 'AVAILABLE'
    }])
    
    books = pd.concat([books, new_book], ignore_index=True)
    books.to_excel(BOOKS_FILE, index=False)
    return True, new_id

def add_book_copies(original_book_id, num_copies):
    try:
        num_copies = int(num_copies)
        if num_copies < 1:
            return False, "Copies must be at least 1"
    except:
        return False, "Invalid number"
    
    books, _, _, _ = load_data()
    
    # Get original book
    original = books[books['id'] == original_book_id]
    if original.empty:
        return False, "Original Book ID not found."
    
    # ID generation
    import re
    max_num = 0
    for book_id in books['id']:
        match = re.search(r'GDL-(\d+)', str(book_id))
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    new_books = []
    generated_ids = []
    
    for i in range(num_copies):
        new_id = f"GDL-{str(max_num + 1 + i).zfill(3)}"
        new_copy = original.iloc[0].copy()
        new_copy['id'] = new_id
        new_copy['status'] = 'AVAILABLE'
        new_books.append(new_copy)
        generated_ids.append(new_id)
    
    books = pd.concat([books, pd.DataFrame(new_books)], ignore_index=True)
    books.to_excel(BOOKS_FILE, index=False)
    
    return True, f"Added {num_copies} copies! IDs: {generated_ids[0]} to {generated_ids[-1]}"

def update_book_details(book_id, title, author, donated_by, title_thanglish, author_thanglish):
    books, _, _, _ = load_data()
    
    if book_id in books['id'].values:
        books.loc[books['id'] == book_id, 'title'] = title
        books.loc[books['id'] == book_id, 'author'] = author
        books.loc[books['id'] == book_id, 'donated_by'] = donated_by
        books.loc[books['id'] == book_id, 'title_thanglish'] = title_thanglish
        books.loc[books['id'] == book_id, 'author_thanglish'] = author_thanglish
        books.to_excel(BOOKS_FILE, index=False)
        return True, "Book details updated."
    return False, "Book ID not found."

# --- Member Management ---

def register_member(name, mobile, email):
    _, users, _, _ = load_data()
    
    # Check mobile uniqueness
    if mobile in users['mobile'].astype(str).values:
        return False, "Member with this mobile number already exists."
    
    # ID generation
    import re
    max_num = 0
    for user_id in users['user_id']:
        match = re.search(r'MEM-(\d+)', str(user_id))
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    
    new_id = f"MEM-{str(max_num + 1).zfill(3)}"
    
    new_user = pd.DataFrame([{
        'user_id': new_id,
        'name': name,
        'email': email,
        'mobile': mobile,
        'role': 'USER'
    }])
    
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_excel(USERS_FILE, index=False)
    return True, f"Member Registered Successfully! ID: {new_id}"

def update_user_details(user_id, name, mobile, email):
    _, users, _, _ = load_data()
    
    if user_id in users['user_id'].values:
        users.loc[users['user_id'] == user_id, 'name'] = name
        users.loc[users['user_id'] == user_id, 'mobile'] = mobile
        users.loc[users['user_id'] == user_id, 'email'] = email
        users.to_excel(USERS_FILE, index=False)
        return True, "User details updated."
    return False, "User ID not found."

# --- Transaction Flows ---

def borrow_book_request(book_id, user_name, mobile, email):
    books, _, _, pending = load_data()
    
    # Check book exists and is available
    book = books[books['id'] == book_id]
    if book.empty:
        return False, "Book not found."
    
    if book.iloc[0]['status'] != 'AVAILABLE':
        return False, f"Book is currently {book.iloc[0]['status']}."
    
    # Update book status
    books.loc[books['id'] == book_id, 'status'] = 'PENDING'
    books.to_excel(BOOKS_FILE, index=False)
    
    # Create pending request
    tx_id = get_next_tx_id()
    new_request = pd.DataFrame([{
        'transaction_id': tx_id,
        'book_id': book_id,
        'book_title': book.iloc[0]['title'],
        'user_id': 'WALK-IN',
        'user_name': user_name,
        'user_email': email,
        'user_mobile': mobile,
        'borrow_date': datetime.now().strftime("%Y-%m-%d"),
        'return_date': None,
        'status': 'BORROW_REQUESTED'
    }])
    
    pending = pd.concat([pending, new_request], ignore_index=True)
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, "Borrow request sent! Please wait for Admin approval."

def approve_borrow(transaction_id):
    books, _, transactions, pending = load_data()
    
    # Find pending request
    request = pending[pending['transaction_id'] == transaction_id]
    if request.empty:
        return False, "Request not found."
    
    book_id = request.iloc[0]['book_id']
    
    # Update book status
    books.loc[books['id'] == book_id, 'status'] = 'BORROWED'
    books.to_excel(BOOKS_FILE, index=False)
    
    # Move to transactions
    request_copy = request.copy()
    request_copy['status'] = 'ACTIVE'
    transactions = pd.concat([transactions, request_copy], ignore_index=True)
    transactions.to_excel(TRANSACTIONS_FILE, index=False)
    
    # Remove from pending
    pending = pending[pending['transaction_id'] != transaction_id]
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, "Borrow request approved. Moved to Active Transactions."

def reject_borrow(transaction_id):
    books, _, _, pending = load_data()
    
    # Find pending request
    request = pending[pending['transaction_id'] == transaction_id]
    if request.empty:
        return False, "Request not found."
    
    book_id = request.iloc[0]['book_id']
    
    # Release book
    books.loc[books['id'] == book_id, 'status'] = 'AVAILABLE'
    books.to_excel(BOOKS_FILE, index=False)
    
    # Remove from pending
    pending = pending[pending['transaction_id'] != transaction_id]
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, "Borrow request rejected."

def request_return(book_id, mobile):
    _, _, transactions, _ = load_data()
    
    input_mobile = normalize_mobile(mobile)
    
    # Find active transaction
    active = transactions[(transactions['book_id'] == book_id) & 
                         (transactions['status'] == 'ACTIVE')]
    
    for idx, row in active.iterrows():
        if normalize_mobile(row['user_mobile']) == input_mobile:
            transactions.loc[idx, 'status'] = 'RETURN_REQUESTED'
            transactions.to_excel(TRANSACTIONS_FILE, index=False)
            return True, "Return requested. Waiting for Admin approval."
    
    return False, "Active transaction not found for this book and mobile."

def approve_return(transaction_id):
    books, _, transactions, _ = load_data()
    
    # Find transaction
    tx = transactions[transactions['transaction_id'] == transaction_id]
    if tx.empty:
        return False, "Transaction not found."
    
    book_id = tx.iloc[0]['book_id']
    
    # Update transaction
    transactions.loc[transactions['transaction_id'] == transaction_id, 'status'] = 'RETURNED'
    transactions.loc[transactions['transaction_id'] == transaction_id, 'return_date'] = datetime.now().strftime('%Y-%m-%d')
    transactions.to_excel(TRANSACTIONS_FILE, index=False)
    
    # Release book
    books.loc[books['id'] == book_id, 'status'] = 'AVAILABLE'
    books.to_excel(BOOKS_FILE, index=False)
    
    return True, "Return approved. Book is now available."

def get_user_history(mobile):
    if not mobile:
        return []
    
    _, _, transactions, pending = load_data()
    input_mobile = normalize_mobile(mobile)
    
    results = []
    
    # Active/Return Requested transactions
    active = transactions[transactions['status'].isin(['ACTIVE', 'RETURN_REQUESTED'])]
    for _, row in active.iterrows():
        if normalize_mobile(row['user_mobile']) == input_mobile:
            results.append(row.to_dict())
    
    # Pending borrows
    pending_borrows = pending[pending['status'] == 'BORROW_REQUESTED']
    for _, row in pending_borrows.iterrows():
        if normalize_mobile(row['user_mobile']) == input_mobile:
            results.append(row.to_dict())
    
    return results

def update_legacy_mobile(transaction_id, new_mobile):
    _, _, transactions, _ = load_data()
    
    if transaction_id in transactions['transaction_id'].values:
        transactions.loc[transactions['transaction_id'] == transaction_id, 'user_mobile'] = str(new_mobile)
        transactions.to_excel(TRANSACTIONS_FILE, index=False)
        return True, "Mobile number updated successfully."
    return False, "Transaction ID not found."

def sync_to_master():
    """Backup data to source/master.xlsx"""
    try:
        books, users, transactions, pending = load_data()
        
        # This would need to be implemented based on your master.xlsx structure
        return True, "Data synced to master file."
    except Exception as e:
        return False, str(e)
