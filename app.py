import streamlit as st
import pandas as pd
import data_manager as dm
from st_keyup import st_keyup

st.set_page_config(page_title="வாசகர் வட்டம் / Bibliophiles📚📖 ", layout="wide")

# Hide GitHub icon and menu
hide_menu_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)

# Session State Initialization
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'user'
if 'authenticated_user' not in st.session_state:
    st.session_state['authenticated_user'] = None
if 'admin_authenticated' not in st.session_state:
    st.session_state['admin_authenticated'] = False

# --- DIALOGS (Global Scope to avoid Nesting Errors) ---

@st.dialog("Request to Lend")
def lend_dialog(book_id, book_title):
    st.write(f"Requesting: **{book_title}** ({book_id})")
    
    # --- Auto-Fill State Management ---
    # Use keys directly bound to the input widgets
    if 'dlg_lend_name' not in st.session_state: st.session_state.dlg_lend_name = ""
    if 'dlg_lend_mobile' not in st.session_state: st.session_state.dlg_lend_mobile = ""
    if 'dlg_lend_email' not in st.session_state: st.session_state.dlg_lend_email = ""
    
    # Step 1: Member Lookup (Optional)
    col_mem1, col_mem2 = st.columns([3, 1])
    with col_mem1:
        mem_id_input = st.text_input("Member ID (Optional)", placeholder="e.g. MEM-005")
    with col_mem2:
        st.write("")
        st.write("")
        # We use a key for the button to avoid any potential reload ambiguity
        if st.button("Check", key="btn_check_mem"):
            if mem_id_input:
                mem = dm.get_member_by_id(mem_id_input)
                if mem:
                    # Update the session state keys bound to the widgets
                    st.session_state.dlg_lend_name = mem['name']
                    # Normalize mobile to remove .0 and ensure string
                    st.session_state.dlg_lend_mobile = dm.normalize_mobile(mem['mobile'])
                    st.session_state.dlg_lend_email = str(mem['email']) if pd.notna(mem['email']) else ""
                    st.success(f"Found: {mem['name']}")
                    # Do NOT rerun here. Streamlit updates the widget values automatically via session state binding.
                else:
                    st.error("Member ID not found.")
    
    st.divider()
    
    # Step 2: Details Form
    with st.form("lend_form"):
        # Bind inputs to session state keys
        name = st.text_input("Your Name", key="dlg_lend_name")
        mobile = st.text_input("Mobile Number", max_chars=10, placeholder="10 digit number", key="dlg_lend_mobile")
        email = st.text_input("Email Address", key="dlg_lend_email")
        
        st.caption("If you don't have a Member ID, just fill above. We'll register you automatically!")
        
        submitted = st.form_submit_button("Send Request")
        
        if submitted:
            if not name or not mobile:
                st.error("Name and Mobile are required.")
            elif not mobile.isdigit() or len(mobile) != 10:
                st.error("Mobile number must be exactly 10 digits.")
            else:
                # Allow passing member_id if it was verified
                mid = mem_id_input if mem_id_input else None
                success, msg = dm.lend_book_request(book_id, name, mobile, email, member_id=mid)
                if success:
                    st.success(msg)
                    # Clear state for next time
                    del st.session_state.dlg_lend_name
                    del st.session_state.dlg_lend_mobile
                    del st.session_state.dlg_lend_email
                    # Rerun to close the dialog and refresh main page
                    st.rerun()
                else:
                    st.error(msg)

@st.dialog("Express Interest")
def interest_dialog(book_id, book_title):
    st.write(f"Book: **{book_title}** ({book_id})")
    st.warning("This book is currently lent out. We'll notify the admin of your interest.")
    with st.form("interest_form"):
        name = st.text_input("Your Name")
        mobile = st.text_input("Mobile Number", max_chars=10, placeholder="10 digit number")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Submit Interest")
        
        if submitted:
            if not name or not mobile or not email:
                st.error("All fields are required.")
            elif not mobile.isdigit() or len(mobile) != 10:
                st.error("Mobile number must be exactly 10 digits.")
            else:
                success, msg = dm.express_interest(book_id, book_title, name, mobile, email)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)


# --- HEADER ---
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.session_state.view_mode == 'user':
        if st.button("🔑 Admin Portal", use_container_width=True):
            st.session_state.view_mode = 'admin'
            st.rerun()
    else:
        if st.button("🏠 User Portal", use_container_width=True):
            st.session_state.view_mode = 'user'
            st.rerun()

# --- ADMIN PORTAL ---
if st.session_state.view_mode == "admin":
    with col1:
        st.title("Admin Portal")
    
    # Login
    if not st.session_state['admin_authenticated']:
        st.subheader("Login")
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("Login"):
            if password == "admin123":
                st.session_state['admin_authenticated'] = True
                st.rerun()
            else:
                st.error("Incorrect password")
    else:
        if st.sidebar.button("Logout Admin"):
            st.session_state['admin_authenticated'] = False
            st.rerun()
            
        tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Manage Books", "Manage Members", "Database Sync"])
        
        books, users, transactions, pending = dm.load_data()
        
        with tab1:
            st.header("Dashboard")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Books", len(books))
            col2.metric("Active Loans", len(transactions[transactions['status'] == 'ACTIVE']))
            # Lend requests in pending, Return requests in transactions
            col3.metric("Pending Actions", len(pending) + len(transactions[transactions['status'] == 'RETURN_REQUESTED']))
            
            st.divider()
            
            # --- APPROVAL QUEUE ---
            st.subheader("📋 Approval Queue")
            
            # Filter pending requests
            # pending dataframe holds BORROW_REQUESTED
            pending_lends = pending
            pending_returns = transactions[transactions['status'] == 'RETURN_REQUESTED']
            
            q_tab1, q_tab2 = st.tabs([f"Lend Requests ({len(pending_lends)})", f"Return Requests ({len(pending_returns)})"])
            
            with q_tab1:
                if not pending_lends.empty:
                    for idx, row in pending_lends.iterrows():
                        with st.container():
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                            c1.write(f"**{row['book_title']}**")
                            c1.caption(f"ID: {row['book_id']}")
                            c2.write(f"User: {row['user_name']}\nMobile: {row['user_mobile']}")
                            
                            if c3.button("Approve", key=f"app_bor_{row['transaction_id']}"):
                                success, msg = dm.approve_lend(row['transaction_id'])
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else: st.error(msg)
                                
                            if c4.button("Reject", key=f"rej_bor_{row['transaction_id']}"):
                                success, msg = dm.reject_lend(row['transaction_id'])
                                if success:
                                    st.warning(msg)
                                    st.rerun()
                                else: st.error(msg)
                            st.divider()
                else:
                    st.info("No pending lend requests.")

            with q_tab2:
                if not pending_returns.empty:
                    for idx, row in pending_returns.iterrows():
                        with st.container():
                            c1, c2, c3 = st.columns([3, 3, 2])
                            c1.write(f"**{row['book_title']}**")
                            c1.caption(f"ID: {row['book_id']}")
                            c2.write(f"User: {row['user_name']} ({row['user_mobile']})")
                            
                            if c3.button("Approve Return", key=f"app_ret_{row['transaction_id']}"):
                                success, msg = dm.approve_return(row['transaction_id'])
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else: st.error(msg)
                            st.divider()
                else:
                    st.info("No pending return requests.")

            st.divider()
            
            # Legacy Data Fix
            with st.expander("🛠 Fix Legacy Data (Link Mobile)"):
                st.write("Link a mobile number to an old transaction so the user can see it in 'My Account'.")
                with st.form("fix_legacy_form"):
                    c_fix1, c_fix2 = st.columns(2)
                    with c_fix1:
                        fix_tx_id = st.text_input("Transaction ID (from table below)")
                    with c_fix2:
                        fix_mobile = st.text_input("New Mobile Number")
                    
                    if st.form_submit_button("Update Mobile Number"):
                        if fix_tx_id and fix_mobile:
                            success, msg = dm.update_legacy_mobile(fix_tx_id, fix_mobile)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

            st.divider()
            
            # --- TABLES ---
            t_tab1, t_tab2 = st.tabs(["Active Loans", "All Transactions"])
            
            with t_tab1:
                col_search1, col_search2 = st.columns(2)
                with col_search1:
                     s_loan_book = st.text_input("Search Book Title/ID", key="s_loan_book")
                with col_search2:
                     s_loan_user = st.text_input("Search User Name/Mobile", key="s_loan_user")
                
                active_loans = transactions[transactions['status'] == 'ACTIVE']
                
                # Apply filters
                if s_loan_book:
                    active_loans = active_loans[
                        active_loans['book_title'].str.contains(s_loan_book, case=False, na=False) |
                        active_loans['book_id'].str.contains(s_loan_book, case=False, na=False)
                    ]
                if s_loan_user:
                    active_loans = active_loans[
                        active_loans['user_name'].str.contains(s_loan_user, case=False, na=False) |
                        active_loans['user_mobile'].astype(str).str.contains(s_loan_user, case=False, na=False)
                    ]
                
                # ... (Search filters logic) ...
                
                # We need user_id to perform updates, so include it in data but maybe configure column to be read-only or hidden
                result_active = active_loans[['transaction_id', 'book_title', 'user_id', 'user_name', 'user_mobile', 'borrow_date']].copy()
                
                edited_active = st.data_editor(
                    result_active,
                    hide_index=True,
                    use_container_width=True,
                    key="editor_active_loans",
                    disabled=['transaction_id', 'book_title', 'user_id', 'user_name', 'borrow_date'] # Only mobile editable
                )
                
                # Check for changes
                if not result_active.equals(edited_active):
                    # Find changed rows
                    # We iterate to find where mobile changed
                    for index, row in edited_active.iterrows():
                        original_row = result_active.loc[index]
                        if str(row['user_mobile']) != str(original_row['user_mobile']):
                            # Mobile changed
                            user_id = row['user_id']
                            new_mobile = row['user_mobile']
                            
                            # Fetch current details to preserve name/email
                            # (Or we could assume table name is correct, but email is missing from this view)
                            curr_mem = dm.get_member_by_id(user_id)
                            if curr_mem:
                                # Update
                                success, msg = dm.update_user_details(
                                    user_id, 
                                    curr_mem['name'], 
                                    new_mobile, 
                                    curr_mem['email']
                                )
                                if success:
                                    st.success(f"Updated {curr_mem['name']}: {msg}")
                                    st.rerun()
                                else:
                                    st.error(msg)
            
            with t_tab2:
                # All Transactions Editor
                st.write("Double-click **User Mobile** to update.")
                # Ensure all cols are present
                
                edited_all_tx = st.data_editor(
                    transactions,
                    use_container_width=True,
                    key="editor_all_tx",
                    disabled=[c for c in transactions.columns if c != 'user_mobile']
                )
                
                if not transactions.equals(edited_all_tx):
                     for index, row in edited_all_tx.iterrows():
                        original_row = transactions.loc[index]
                        if str(row['user_mobile']) != str(original_row['user_mobile']):
                            user_id = row['user_id']
                            new_mobile = row['user_mobile']
                            
                            if pd.isna(user_id) or user_id == 'WALK-IN':
                                # Can we update walk-in? 
                                # If it's legacy/walk-in without ID, we can only update the transaction record directly?
                                # But the user asked to "update respective user".
                                # If WALK-IN, maybe just update the transaction using update_legacy_mobile?
                                success, msg = dm.update_legacy_mobile(row['transaction_id'], new_mobile)
                                if success: st.success(msg); st.rerun()
                            else:
                                curr_mem = dm.get_member_by_id(user_id)
                                if curr_mem:
                                    success, msg = dm.update_user_details(
                                        user_id, 
                                        curr_mem['name'], 
                                        new_mobile, 
                                        curr_mem['email']
                                    )
                                    if success: st.success(msg); st.rerun()
            
        with tab2:
            st.header("Inventory Management")
            
            # Add Book
            with st.expander("Add New Book"):
                # Check for success message from previous run
                if 'add_book_success' in st.session_state:
                    st.success(st.session_state.add_book_success)
                    del st.session_state.add_book_success
                
                with st.form("add_book_form", clear_on_submit=False):
                    c_add1, c_add2 = st.columns(2)
                    with c_add1:
                        new_title = st.text_input("Title (Tamil)", key="ab_title")
                        new_author = st.text_input("Author (Tamil)", key="ab_author")
                    with c_add2:
                        new_t_thang = st.text_input("Title (Thanglish)", key="ab_t_thang")
                        new_a_thang = st.text_input("Author (Thanglish)", key="ab_a_thang")
                        
                    new_donated = st.text_input("Donated By", key="ab_donated")
                    
                    submitted = st.form_submit_button("Add Book")
                    if submitted:
                        if new_title and new_author:
                            success, b_id = dm.add_book(new_title, new_author, new_donated, new_t_thang, new_a_thang)
                            # Store success message in session state
                            st.session_state.add_book_success = f"Added '{new_title}' with ID {b_id}"
                            
                            # Clear form inputs using keys
                            st.session_state.ab_title = ""
                            st.session_state.ab_author = ""
                            st.session_state.ab_t_thang = ""
                            st.session_state.ab_a_thang = ""
                            st.session_state.ab_donated = ""
                            
                            st.rerun()
                        else:
                            st.error("Title and Author (Tamil) are required.")
            
            # Add Copies
            with st.expander("Add Copies (Bulk)"):
                st.write("Create more copies of an existing book. New IDs will be generated.")
                c_copy1, c_copy2 = st.columns([3, 1])
                with c_copy1:
                    src_id = st.text_input("Source Book ID (e.g., GDL-001)")
                with c_copy2:
                    num_copies = st.number_input("Count", min_value=1, value=1)
                
                if st.button("Generate Copies"):
                    if src_id:
                        success, msg = dm.add_book_copies(src_id, num_copies)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else: st.error(msg)
                    else: st.error("Book ID required.")
            
            # Edit Book
            with st.expander("Edit Book Details"):
                c_edit_b1, c_edit_b2 = st.columns([3, 1])
                with c_edit_b1:
                    edit_book_id = st.text_input("Enter Book ID to Edit (e.g., GDL-001)")
                with c_edit_b2:
                    st.write("")
                    st.write("")
                    st.button("Load Book")
                    
                if edit_book_id:
                    book_row = books[books['id'] == edit_book_id]
                    if not book_row.empty:
                        st.info(f"Editing: {book_row.iloc[0]['title']}")
                        with st.form("edit_book_form"):
                            row = book_row.iloc[0]
                            # Handle missing keys safely
                            cur_t_thang = row.get('title_thanglish', "") if pd.notna(row.get('title_thanglish')) else ""
                            cur_a_thang = row.get('author_thanglish', "") if pd.notna(row.get('author_thanglish')) else ""
                            
                            ce1, ce2 = st.columns(2)
                            with ce1:
                                e_title = st.text_input("Title (Tamil)", value=row['title'])
                                e_author = st.text_input("Author (Tamil)", value=row['author'])
                            with ce2:
                                e_t_thang = st.text_input("Title (Thanglish)", value=cur_t_thang)
                                e_a_thang = st.text_input("Author (Thanglish)", value=cur_a_thang)
                                
                            e_donated = st.text_input("Donated By", value=row['donated_by'])
                            
                            c_upd_b, c_del_b = st.columns([3, 1])
                            with c_upd_b:
                                if st.form_submit_button("Update Book Details"):
                                    success, msg = dm.update_book_details(edit_book_id, e_title, e_author, e_donated, e_t_thang, e_a_thang)
                                    if success:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with c_del_b:
                                if st.form_submit_button("Delete Book", type="primary"):
                                    success, msg = dm.delete_book(edit_book_id)
                                    if success:
                                        st.success(msg)
                                        # Clear state if any
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    else:
                        st.warning("Book ID not found.")

            # View/Search Books
            st.subheader("Book List")
            # Upgrade to real-time search
            admin_book_search = st_keyup("Search Inventory (Real-Time)", key="admin_book_search")
            
            if admin_book_search:
                filtered_books = books[
                    books['title'].str.contains(admin_book_search, case=False, na=False) |
                    books['author'].str.contains(admin_book_search, case=False, na=False) |
                    books['id'].str.contains(admin_book_search, case=False, na=False) |
                    books['title_thanglish'].str.contains(admin_book_search, case=False, na=False) |
                    books['author_thanglish'].str.contains(admin_book_search, case=False, na=False)
                ]
                st.dataframe(filtered_books, use_container_width=True)
            else:
                st.dataframe(books, use_container_width=True)

        with tab3:
            st.header("Member Management")
            
            # Register Member
            with st.expander("Register New Member"):
                # Check for success message from previous run
                if 'reg_mem_success' in st.session_state:
                    st.success(st.session_state.reg_mem_success)
                    del st.session_state.reg_mem_success
                
                with st.form("reg_member_form"):
                    m_name = st.text_input("Name", key="reg_m_name")
                    m_mobile = st.text_input("Mobile Number", max_chars=10, placeholder="10 digit number", key="reg_m_mobile")
                    m_email = st.text_input("Email", key="reg_m_email")
                    submitted = st.form_submit_button("Register Member")
                    
                    if submitted:
                        if not m_name or not m_mobile:
                            st.error("Name and Mobile are required.")
                        elif not m_mobile.isdigit() or len(m_mobile) != 10:
                            st.error("Mobile number must be exactly 10 digits.")
                        elif m_name and m_mobile:
                            success, msg = dm.register_member(m_name, m_mobile, m_email)
                            if success:
                                st.session_state.reg_mem_success = msg
                                # Clear form inputs
                                st.session_state.reg_m_name = ""
                                st.session_state.reg_m_mobile = ""
                                st.session_state.reg_m_email = ""
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Name and Mobile are required.")
            
            # Edit Member
            with st.expander("Edit Member Details"):
                c_edit_m1, c_edit_m2 = st.columns([3, 1])
                with c_edit_m1:
                    edit_user_id = st.text_input("Enter Member ID (e.g., MEM-001)")
                with c_edit_m2:
                    st.write("")
                    st.write("")
                    st.button("Load Member")
                    
                if edit_user_id:
                    # Case insensitive lookup
                    user_row = users[users['user_id'].astype(str).str.upper() == edit_user_id.strip().upper()]
                    if not user_row.empty:
                        st.info(f"Editing: {user_row.iloc[0]['name']}")
                        with st.form("edit_user_form"):
                            # Handle potential NaN values
                            curr_name = user_row.iloc[0]['name'] if pd.notna(user_row.iloc[0]['name']) else ""
                            curr_mobile = str(user_row.iloc[0]['mobile']) if pd.notna(user_row.iloc[0]['mobile']) else ""
                            curr_email = str(user_row.iloc[0]['email']) if pd.notna(user_row.iloc[0]['email']) else ""
                            
                            u_name = st.text_input("Name", value=curr_name)
                            u_mobile = st.text_input("Mobile Number", value=dm.normalize_mobile(curr_mobile), max_chars=10, placeholder="10 digit number")
                            u_email = st.text_input("Email", value=curr_email)
                            
                            
                            c_upd, c_del = st.columns([3, 1])
                            with c_upd:
                                if st.form_submit_button("Update Member Details"):
                                    if not u_name or not u_mobile:
                                        st.error("Name and Mobile are required.")
                                    elif not u_mobile.isdigit() or len(u_mobile) != 10:
                                        st.error("Mobile number must be exactly 10 digits.")
                                    else:
                                        success, msg = dm.update_user_details(user_row.iloc[0]['user_id'], u_name, u_mobile, u_email)
                                        if success:
                                            st.success(msg)
                                            # Rerun to show updates immediately
                                            st.rerun() 
                                        else:
                                            st.error(msg)
                            with c_del:
                                # Danger zone
                                if st.form_submit_button("Delete Member", type="primary"):
                                    success, msg = dm.delete_member(edit_user_id)
                                    if success:
                                        st.success(msg)
                                        st.session_state.edit_user_id = "" # Clear selection
                                        st.rerun()
                                    else:
                                        st.error(msg)
                    else:
                        st.warning("Member ID not found.")

            # Member List
            st.subheader("Registered Members")
            member_search = st_keyup("Search Members", key="admin_mem_search")
            
            if member_search:
                filtered_users = users[
                    users['name'].str.contains(member_search, case=False, na=False) |
                    users['mobile'].astype(str).str.contains(member_search, case=False, na=False) |
                    users['email'].str.contains(member_search, case=False, na=False) |
                    users['user_id'].str.contains(member_search, case=False, na=False)
                ]
                st.dataframe(filtered_users, use_container_width=True)
            else:
                st.dataframe(users, use_container_width=True)

        with tab4:
            st.header("Database Management")
            st.write("Current data is stored in `data/`. Clicking below will update `source/master.xlsx`.")
            
            if st.button("Update Base Excel"):
                success, msg = dm.sync_to_master()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# --- USER PORTAL ---
elif st.session_state.view_mode == "user":
    st.title("வாசகர் வட்டம் / Bibliophiles📚📖")
    
    # Custom Navigation Buttons
    if 'user_view' not in st.session_state:
        st.session_state['user_view'] = 'browse'
        
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("📖 BROWSE LIBRARY", use_container_width=True, type="primary" if st.session_state['user_view'] == 'browse' else "secondary"):
            st.session_state['user_view'] = 'browse'
            st.rerun()
    with col_nav2:
        if st.button("👤 MY ACCOUNT & RETURNS", use_container_width=True, type="primary" if st.session_state['user_view'] == 'account' else "secondary"):
            st.session_state['user_view'] = 'account'
            st.rerun()
            
    st.divider()
    
    # --- VIEW: BROWSE ---
    if st.session_state['user_view'] == 'browse':
        st.subheader("Browse Books")
        st.caption("Search and lend books instantly.")
        books, _, _, _ = dm.load_data()
        
        # Search & Filter
        c_title, c_author, c_filter = st.columns([2, 2, 1])
        with c_title:
            search_title = st_keyup("Search Title / ID", key="search_title_input")
        with c_author:
            search_author = st_keyup("Search Author", key="search_author_input")
        with c_filter:
            filter_opt = st.selectbox("Show", ["All Books", "Available Only"])
            
        # Apply Logic
        display_books = books
        # Ensure ID is string for search
        display_books['id'] = display_books['id'].astype(str)
        
        if search_title:
            display_books = display_books[
                display_books['title'].str.contains(search_title, case=False, na=False) |
                display_books['title_thanglish'].str.contains(search_title, case=False, na=False) |
                display_books['id'].str.contains(search_title, case=False, na=False)
            ]
            
        if search_author:
            display_books = display_books[
                display_books['author'].str.contains(search_author, case=False, na=False) |
                display_books['author_thanglish'].str.contains(search_author, case=False, na=False)
            ]

        if filter_opt == "Available Only":
            display_books = display_books[display_books['status'] == 'AVAILABLE']
        
        # Priority Sort: Available First, then Title Ascending
        display_books['sort_order'] = display_books['status'].apply(lambda x: 0 if x == 'AVAILABLE' else 1)
        display_books = display_books.sort_values(by=['sort_order', 'title'], ascending=[True, True])

        # Limit if no search to avoid lag, but allow full list if filtered
        if not search_title and not search_author and filter_opt == "All Books":
             display_books = display_books.head(50)
             st.caption("Showing first 50 items (Available first). Use search for more.")
        else:
             st.caption(f"Found {len(display_books)} books.")
        
        # Grid
        for index, row in display_books.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
                c1.write(f"**{row['title']}**")
                c1.caption(f"ID: {row['id']}")
                c2.write(f"*{row['author']}*")
                
                status = row['status']
                if status == 'AVAILABLE':
                    c3.success(status)
                    if c4.button("📚 Lend", key=f"btn_{row['id']}"):
                        lend_dialog(row['id'], row['title'])
                else:
                    c3.error(status)
                    if c4.button("⭐ Interested", key=f"int_{row['id']}"):
                        interest_dialog(row['id'], row['title'])
                st.divider()

    # --- VIEW: MY ACCOUNT ---
    elif st.session_state['user_view'] == 'account':
        st.header("My Account")
        st.info("Enter your Mobile Number OR Member ID to see your lent books.")
        
        c_acc1, c_acc2, c_acc3 = st.columns([2, 0.5, 2])
        with c_acc1:
            my_mobile = st.text_input("Mobile Number", key="my_acc_mobile")
        with c_acc2:
            st.markdown("<h4 style='text-align: center; padding-top: 20px;'>OR</h4>", unsafe_allow_html=True)
        with c_acc3:
            my_mem_id = st.text_input("Member ID", key="my_acc_mem_id")
            
        st.button("Check Loans", key="btn_check_loans")
        
        identifier = None
        if my_mobile: identifier = my_mobile
        elif my_mem_id: identifier = my_mem_id
        
        if identifier:
            history = dm.get_user_history(identifier)
            if history:
                # Show Member Name from history
                user_name = history[0].get('user_name', 'Unknown')
                st.success(f"Welcome, **{user_name}**!")
                
                st.subheader(f"My Books ({len(history)})")
                for item in history:
                    with st.container():
                        st.write(f"**{item['book_title']}** (ID: {item['book_id']})")
                        st.write(f"Lent Date: {item['borrow_date']}")
                        
                        # Status Logic
                        if item['status'] == 'ACTIVE':
                            st.success("Status: LENT (Active)")
                            # For return, we need mobile number usually. 
                            # If they searched by ID, we might need to fetch mobile from transaction or user?
                            # data_manager.request_return currently needs mobile to verify transaction ownership.
                            # But wait, request_return verifies against transactions table.
                            # The transactions table has 'user_mobile'.
                            # If user viewing by ID, we should try to pass the mobile from the transaction record itself to ensure it matches.
                            
                            tx_mobile = str(item.get('user_mobile', ''))
                            
                            if st.button("Request Return", key=f"ret_{item['transaction_id']}"):
                                success, msg = dm.request_return(item['book_id'], tx_mobile)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        elif item['status'] == 'BORROW_REQUESTED':
                            st.warning("Status: PENDING APPROVAL (Wait for Admin)")
                        elif item['status'] == 'RETURN_REQUESTED':
                            st.info("Status: RETURN PENDING (Wait for Admin)")
                        
                        st.divider()
            else:
                st.write("No active records found. If you have lent books, please ask Admin to check 'Legacy Data'.")
