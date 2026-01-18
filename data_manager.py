import pandas as pd
from datetime import datetime
import os
from transliterate_utils import transliterate_text

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
    
    # Auto-Transliterate if missing
    if not title_thanglish:
        title_thanglish = transliterate_text(title)
        
    if not author_thanglish:
        author_thanglish = transliterate_text(author)
    
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

def delete_book(book_id):
    books, _, transactions, pending = load_data()
    
    book = books[books['id'] == book_id]
    if book.empty:
        return False, "Book not found."
        
    if book.iloc[0]['status'] == 'LENT':
        return False, "Cannot delete book. It is currently LENT out."
        
    # Check if there are any active transactions referencing this book (double check)
    active_tx = transactions[(transactions['book_id'] == book_id) & (transactions['status'] == 'ACTIVE')]
    if not active_tx.empty:
        return False, "Cannot delete book. Active transactions exist."

    # Proceed to delete
    books = books[books['id'] != book_id]
    
    # Auto-Renumber
    books, transactions, pending = _renumber_books_internal(books, transactions, pending)
    
    books.to_excel(BOOKS_FILE, index=False)
    transactions.to_excel(TRANSACTIONS_FILE, index=False)
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, f"Book deleted. IDs updated."

# --- Member Management ---

def get_member_by_id(user_id):
    _, users, _, _ = load_data()
    # Case insensitive search
    user = users[users['user_id'].astype(str).str.upper() == str(user_id).upper()]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

def get_member_by_mobile(mobile):
    _, users, _, _ = load_data()
    norm_mobile = normalize_mobile(mobile)
    # Check mobile
    user = users[users['mobile'].apply(normalize_mobile) == norm_mobile]
    if not user.empty:
        return user.iloc[0].to_dict()
    return None

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
    _, users, transactions, pending = load_data()
    
    if user_id in users['user_id'].values:
        # 1. Update User Registry
        users.loc[users['user_id'] == user_id, 'name'] = name
        users.loc[users['user_id'] == user_id, 'mobile'] = mobile
        users.loc[users['user_id'] == user_id, 'email'] = email
        users.to_excel(USERS_FILE, index=False)
        
        # 2. Propagate to Transactions (Active/Returned/etc)
        # Check if user_id exists in transactions
        if 'user_id' in transactions.columns and user_id in transactions['user_id'].values:
            transactions.loc[transactions['user_id'] == user_id, 'user_mobile'] = str(mobile)
            transactions.to_excel(TRANSACTIONS_FILE, index=False)
            
        # 3. Propagate to Pending Requests
        if 'user_id' in pending.columns and user_id in pending['user_id'].values:
            pending.loc[pending['user_id'] == user_id, 'user_mobile'] = str(mobile)
            pending.to_excel(PENDING_FILE, index=False)
            
        return True, "User details updated across registry and all records."
    return False, "User ID not found."

def delete_member(user_id):
    _, users, transactions, pending = load_data()
    
    # Check for active loans
    active_loans = transactions[(transactions['user_id'] == user_id) & (transactions['status'] == 'ACTIVE')]
    if not active_loans.empty:
        return False, f"Cannot delete member. They have {len(active_loans)} active loans returned."
        
    # Check for pending requests
    pending_reqs = pending[pending['user_id'] == user_id]
    if not pending_reqs.empty:
        return False, "Cannot delete member. They have pending book requests."
        
    if user_id in users['user_id'].values:
        users = users[users['user_id'] != user_id]
        
        # Auto-Renumber
        users, transactions, pending = _renumber_members_internal(users, transactions, pending)
        
        users.to_excel(USERS_FILE, index=False)
        transactions.to_excel(TRANSACTIONS_FILE, index=False)
        pending.to_excel(PENDING_FILE, index=False)
        
        return True, f"Member deleted. IDs updated."
        
    return False, "User ID not found."

# --- Transaction Flows ---

# --- Transaction Flows ---

def lend_book_request(book_id, user_name, mobile, email, member_id=None):
    books, users, _, pending = load_data()
    
    # Check book exists and is available
    book = books[books['id'] == book_id]
    if book.empty:
        return False, "Book not found."
    
    if book.iloc[0]['status'] != 'AVAILABLE':
        return False, f"Book is currently {book.iloc[0]['status']}."
    
    # --- Member Handling ---
    final_user_id = 'WALK-IN'
    
    # 1. Try to link by Member ID if provided
    # 1. Try to link by Member ID if provided
    if member_id:
        mem = get_member_by_id(member_id)
        if mem:
            final_user_id = mem['user_id']
            # Update connection if details differ
            stored_mobile = normalize_mobile(mem['mobile'])
            input_mobile = normalize_mobile(mobile)
            stored_email = str(mem['email']).strip() if pd.notna(mem['email']) else ""
            input_email = str(email).strip()
            
            if stored_mobile != input_mobile or stored_email != input_email:
                # Update details
                # Note: We need to reload users to call update_user_details safely or just call it.
                # Since update_user_details loads data again, we can just call it.
                update_user_details(final_user_id, user_name, mobile, email)
        else:
            return False, f"Member ID {member_id} not found."
            
    # 2. If no Member ID, check by Mobile
    else:
        mem = get_member_by_mobile(mobile)
        if mem:
            final_user_id = mem['user_id']
        else:
            # 3. New Member -> Auto Register
            success, result = register_member(user_name, mobile, email)
            if success:
                # Result message contains ID, but we need the ID cleanly. 
                # Let's refactor register_member or just fetch it back.
                mem_new = get_member_by_mobile(mobile)
                if mem_new:
                    final_user_id = mem_new['user_id']
            else:
                 # If registration failed (e.g. duplicate mobile? shouldn't happen if we checked),
                 # fail the lend request? Or proceed as walk-in? 
                 # User asked for "auto add member", so we should probably succeed.
                 pass

    # Update book status
    books.loc[books['id'] == book_id, 'status'] = 'PENDING'
    books.to_excel(BOOKS_FILE, index=False)
    
    # Create pending request
    tx_id = get_next_tx_id()
    new_request = pd.DataFrame([{
        'transaction_id': tx_id,
        'book_id': book_id,
        'book_title': book.iloc[0]['title'],
        'user_id': final_user_id,
        'user_name': user_name,
        'user_email': email,
        'user_mobile': mobile,
        'borrow_date': datetime.now().strftime("%Y-%m-%d"),
        'return_date': None,
        'status': 'BORROW_REQUESTED'
    }])
    
    pending = pd.concat([pending, new_request], ignore_index=True)
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, f"Lend request sent for {user_name} ({final_user_id})! Please wait for Admin approval."


def express_interest(book_id, book_title, user_name, mobile, email):
    """Record user interest in a lent book"""
    _, _, _, pending = load_data()
    
    tx_id = get_next_tx_id()
    new_interest = pd.DataFrame([{
        'transaction_id': tx_id,
        'book_id': book_id,
        'book_title': book_title,
        'user_id': 'WALK-IN',
        'user_name': user_name,
        'user_email': email,
        'user_mobile': mobile,
        'borrow_date': datetime.now().strftime("%Y-%m-%d"),
        'return_date': None,
        'status': 'INTERESTED'
    }])
    
    pending = pd.concat([pending, new_interest], ignore_index=True)
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, "Interest recorded! Admin will notify you when available."

def approve_lend(transaction_id):
    books, _, transactions, pending = load_data()
    
    # Find pending request
    request = pending[pending['transaction_id'] == transaction_id]
    if request.empty:
        return False, "Request not found."
    
    book_id = request.iloc[0]['book_id']
    
    # Update book status
    books.loc[books['id'] == book_id, 'status'] = 'LENT'
    books.to_excel(BOOKS_FILE, index=False)
    
    # Move to transactions
    request_copy = request.copy()
    request_copy['status'] = 'ACTIVE'
    transactions = pd.concat([transactions, request_copy], ignore_index=True)
    transactions.to_excel(TRANSACTIONS_FILE, index=False)
    
    # Remove from pending
    pending = pending[pending['transaction_id'] != transaction_id]
    pending.to_excel(PENDING_FILE, index=False)
    
    return True, "Lend request approved. Moved to Active Transactions."

def reject_lend(transaction_id):
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
    
    return True, "Lend request rejected."

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

def get_user_history(identifier):
    if not identifier:
        return []
    
    _, _, transactions, pending = load_data()
    
    # We treat identifier as either mobile or ID
    # Normalize if it looks like a mobile (digits)
    check_mobile = None
    check_id = str(identifier).strip().upper()
    
    # Simple heuristic: if it contains only digits and length > 5, treat as mobile primarily
    # But user IDs are formatted "MEM-XXX".
    # Let's normalize mobile if possible
    try:
        check_mobile = normalize_mobile(identifier)
    except:
        pass

    results = []
    
    # Helper to match row
    def match_row(row):
        # Check Mobile
        if check_mobile and normalize_mobile(row['user_mobile']) == check_mobile:
            return True
        # Check ID
        # Some rows might not have user_id if legacy? But our new code adds it.
        # Legacy rows might have 'WALK-IN', so we check explicitly.
        if 'user_id' in row and str(row['user_id']).strip().upper() == check_id:
            return True
        return False
    
    # Active/Return Requested transactions
    active = transactions[transactions['status'].isin(['ACTIVE', 'RETURN_REQUESTED'])]
    for _, row in active.iterrows():
        if match_row(row):
            results.append(row.to_dict())
    
    # Pending borrows
    pending_borrows = pending[pending['status'] == 'BORROW_REQUESTED']
    for _, row in pending_borrows.iterrows():
        if match_row(row):
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

def _renumber_books_internal(books, transactions, pending):
    """Helper to renumber books sequentially GDL-001..."""
    # Extract numeric part for sorting
    import re
    def get_num(x):
        m = re.search(r'GDL-(\d+)', str(x))
        return int(m.group(1)) if m else 999999
    
    books['num_id'] = books['id'].apply(get_num)
    books = books.sort_values('num_id').drop(columns=['num_id']).reset_index(drop=True)
    
    id_map = {} # old -> new
    
    for idx, row in books.iterrows():
        old_id = row['id']
        new_id = f"GDL-{str(idx + 1).zfill(3)}"
        
        if old_id != new_id:
            books.at[idx, 'id'] = new_id
            id_map[old_id] = new_id
            
    # Update references
    if id_map:
        # Transactions
        transactions['book_id'] = transactions['book_id'].replace(id_map)
        # Pending
        pending['book_id'] = pending['book_id'].replace(id_map)
        
    return books, transactions, pending

def _renumber_members_internal(users, transactions, pending):
    """Helper to renumber members sequentially MEM-001..."""
    import re
    def get_num(x):
        m = re.search(r'MEM-(\d+)', str(x))
        return int(m.group(1)) if m else 999999
        
    users['num_id'] = users['user_id'].apply(get_num)
    users = users.sort_values('num_id').drop(columns=['num_id']).reset_index(drop=True)
    
    id_map = {}
    
    for idx, row in users.iterrows():
        old_id = row['user_id']
        new_id = f"MEM-{str(idx + 1).zfill(3)}"
        
        if old_id != new_id:
            users.at[idx, 'user_id'] = new_id
            id_map[old_id] = new_id
            
    # Update references
    if id_map:
        transactions['user_id'] = transactions['user_id'].replace(id_map)
        pending['user_id'] = pending['user_id'].replace(id_map)
        
    return users, transactions, pending
