import requests
import pandas as pd
import json

try:
    # Fetch all stocks without filters (default min_score=0, max_score=100)
    response = requests.get("http://localhost:8000/api/stocks?limit=1000")
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        
        if not df.empty:
            print(f"Total stocks: {len(df)}")
            print("\nScore Distribution:")
            print(df['super_score'].describe())
            
            print("\nStocks with score <= 5:")
            low_score = df[df['super_score'] <= 5]
            print(f"Count: {len(low_score)}")
            if not low_score.empty:
                print(low_score[['papel', 'super_score']].head())
                
            print("\nStocks with score <= 10:")
            low_score_10 = df[df['super_score'] <= 10]
            print(f"Count: {len(low_score_10)}")
            
            print("\nStocks with score <= 20:")
            low_score_20 = df[df['super_score'] <= 20]
            print(f"Count: {len(low_score_20)}")
            
        else:
            print("No data returned.")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Failed to connect: {e}")
