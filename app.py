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
                active_loans = transactions[transactions['status'] == 'ACTIVE']
                st.data_editor(
                    active_loans[['transaction_id', 'book_title', 'user_name', 'user_mobile', 'borrow_date']],
                    hide_index=True,
                    use_container_width=True
                )
            
            with t_tab2:
                st.dataframe(transactions, use_container_width=True)
            
        with tab2:
            st.header("Inventory Management")
            
            # Add Book
            with st.expander("Add New Book"):
                with st.form("add_book_form"):
                    c_add1, c_add2 = st.columns(2)
                    with c_add1:
                        new_title = st.text_input("Title (Tamil)")
                        new_author = st.text_input("Author (Tamil)")
                    with c_add2:
                        new_t_thang = st.text_input("Title (Thanglish)")
                        new_a_thang = st.text_input("Author (Thanglish)")
                        
                    new_donated = st.text_input("Donated By")
                    
                    submitted = st.form_submit_button("Add Book")
                    if submitted:
                        if new_title and new_author:
                            success, b_id = dm.add_book(new_title, new_author, new_donated, new_t_thang, new_a_thang)
                            st.success(f"Added '{new_title}' with ID {b_id}")
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
                            
                            if st.form_submit_button("Update Book Details"):
                                success, msg = dm.update_book_details(edit_book_id, e_title, e_author, e_donated, e_t_thang, e_a_thang)
                                if success:
                                    st.success(msg)
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
                with st.form("reg_member_form"):
                    m_name = st.text_input("Name")
                    m_mobile = st.text_input("Mobile Number", max_chars=10, placeholder="10 digit number")
                    m_email = st.text_input("Email")
                    submitted = st.form_submit_button("Register Member")
                    
                    if submitted:
                        if not m_name or not m_mobile:
                            st.error("Name and Mobile are required.")
                        elif not m_mobile.isdigit() or len(m_mobile) != 10:
                            st.error("Mobile number must be exactly 10 digits.")
                        elif m_name and m_mobile:
                            success, msg = dm.register_member(m_name, m_mobile, m_email)
                            if success:
                                st.success(msg)
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
                    user_row = users[users['user_id'] == edit_user_id]
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
                            
                            if st.form_submit_button("Update Member Details"):
                                if not u_name or not u_mobile:
                                    st.error("Name and Mobile are required.")
                                elif not u_mobile.isdigit() or len(u_mobile) != 10:
                                    st.error("Mobile number must be exactly 10 digits.")
                                else:
                                    success, msg = dm.update_user_details(edit_user_id, u_name, u_mobile, u_email)
                                    if success:
                                        st.success(msg)
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
            
        # Limit if no search to avoid lag, but allow full list if filtered
        if not search_title and not search_author and filter_opt == "All Books":
             display_books = display_books.head(50)
             st.caption("Showing first 50 items. Use search for more.")
        else:
             st.caption(f"Found {len(display_books)} books.")

        # Lend Dialog
        @st.dialog("Request to Lend")
        def lend_dialog(book_id, book_title):
            st.write(f"Requesting: **{book_title}** ({book_id})")
            st.info("Your request will be sent to the Admin for approval.")
            with st.form("lend_form"):
                name = st.text_input("Your Name")
                mobile = st.text_input("Mobile Number", max_chars=10, placeholder="10 digit number")
                email = st.text_input("Email Address")
                submitted = st.form_submit_button("Send Request")
                
                if submitted:
                    if not name or not mobile or not email:
                        st.error("All fields are required.")
                    elif not mobile.isdigit() or len(mobile) != 10:
                        st.error("Mobile number must be exactly 10 digits.")
                    else:
                        success, msg = dm.lend_book_request(book_id, name, mobile, email)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
        
        # Interest Dialog
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
        st.info("Enter your Mobile Number to see your lent books and request returns.")
        
        c_acc1, c_acc2 = st.columns([3, 1])
        with c_acc1:
            my_mobile = st.text_input("Enter Mobile Number", key="my_acc_mobile")
        with c_acc2:
            st.write("") # Vertical spacer
            st.write("") 
            # Button triggers rerun, which processes the text input
            st.button("Check Loans")
        
        if my_mobile:
            history = dm.get_user_history(my_mobile)
            if history:
                st.subheader(f"My Books ({len(history)})")
                for item in history:
                    with st.container():
                        st.write(f"**{item['book_title']}** (ID: {item['book_id']})")
                        st.write(f"Lent Date: {item['borrow_date']}")
                        
                        # Status Logic
                        if item['status'] == 'ACTIVE':
                            st.success("Status: LENT (Active)")
                            if st.button("Request Return", key=f"ret_{item['transaction_id']}"):
                                success, msg = dm.request_return(item['book_id'], my_mobile)
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
