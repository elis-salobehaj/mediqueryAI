import pandas as pd
import random
import os

# States weighted somewhat towards larger populations
STATES = [
    'CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI',
    'NJ', 'VA', 'WA', 'AZ', 'MA', 'TN', 'IN', 'MO', 'MD', 'WI',
    'CO', 'MN', 'SC', 'AL', 'LA', 'KY', 'OR', 'OK', 'CT', 'UT',
    'IA', 'NV', 'AR', 'MS', 'KS', 'NM', 'NE', 'ID', 'WV', 'HI',
    'NH', 'ME', 'MT', 'RI', 'DE', 'SD', 'ND', 'AK', 'VT', 'WY'
]

# Weights roughly approx population distribution (very simplified)
WEIGHTS = [12, 9, 7, 6, 4, 4, 4, 3, 3, 3] + [1] * 40

def enrich_data():
    csv_path = 'data/patients.csv'
    
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} rows.")

        if 'state' not in df.columns:
            print("Adding 'state' column...")
            # Assign random states
            df['state'] = [random.choices(STATES, weights=WEIGHTS)[0] for _ in range(len(df))]
            
            # Save back
            df.to_csv(csv_path, index=False)
            print("Successfully saved patients.csv with state column.")
            print(df.head())
        else:
            print("'state' column already exists.")

    except Exception as e:
        print(f"Error enriching data: {e}")

if __name__ == "__main__":
    enrich_data()
