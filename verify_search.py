import pandas as pd

def verify_search_logic():
    # Mock Data
    data = {
        'title': ['பொன்னியின் செல்வன்', 'Other Book'],
        'title_thanglish': ['Ponniyin Selvan', 'Other Book'],
        'id': ['GDL-001', 'GDL-002']
    }
    df = pd.DataFrame(data)
    
    print("Testing Search Logic...")
    
    # Test 1: Search by Tamil
    q1 = "பொன்னியின்"
    res1 = df[
        df['title'].str.contains(q1, case=False, na=False) |
        df['title_thanglish'].str.contains(q1, case=False, na=False) |
        df['id'].str.contains(q1, case=False, na=False)
    ]
    print(f"Search '{q1}': Found {len(res1)} (Expected 1)")
    
    # Test 2: Search by Thanglish
    q2 = "Ponniyin"
    res2 = df[
        df['title'].str.contains(q2, case=False, na=False) |
        df['title_thanglish'].str.contains(q2, case=False, na=False) |
        df['id'].str.contains(q2, case=False, na=False)
    ]
    print(f"Search '{q2}': Found {len(res2)} (Expected 1)")
    
    # Test 3: Search by Partial Thanglish case insensitive
    q3 = "ponni"
    res3 = df[
        df['title'].str.contains(q3, case=False, na=False) |
        df['title_thanglish'].str.contains(q3, case=False, na=False) |
        df['id'].str.contains(q3, case=False, na=False)
    ]
    print(f"Search '{q3}': Found {len(res3)} (Expected 1)")

if __name__ == "__main__":
    verify_search_logic()
