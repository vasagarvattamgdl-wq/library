import pandas as pd

try:
    print("--- Source File (Row 64-68) ---")
    df_source = pd.read_excel("source/master.xlsx")
    # Adjust for 0-index: Excel row 66 is index 64 or 65 depending on header. 
    # Usually header is row 1. So row 66 is index 64.
    print(df_source.iloc[63:68].to_string())

    print("\n--- Transactions File (All Active) ---")
    df_tx = pd.read_excel("data/transactions.xlsx")
    # Print rows where user_name matches the one from source or just tail
    print(df_tx.tail(10).to_string())
    
    print("\n--- Mobile Column Analysis ---")
    print(df_tx[['user_name', 'user_mobile']].head(10))
    
except Exception as e:
    print(e)
