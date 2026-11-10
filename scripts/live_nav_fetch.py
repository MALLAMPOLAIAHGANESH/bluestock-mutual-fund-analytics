import requests
import pandas as pd
import os
from datetime import datetime

# List of schemes with their AMFI codes
schemes = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip": 119551,
    "ICICI Bluechip": 120503,
    "Nippon Large Cap": 118632,
    "Axis Bluechip": 119092,
    "Kotak Bluechip": 120841
}

# Path where CSV files will be saved
output_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')

print("="*80)
print("LIVE NAV FETCHING SCRIPT")
print("="*80)
print(f"\nTotal schemes to fetch: {len(schemes)}\n")

# Loop through each scheme and fetch NAV data
for scheme_name, amfi_code in schemes.items():
    try:
        # API endpoint
        url = f"https://api.mfapi.in/mf/{amfi_code}"
        
        print(f"Fetching: {scheme_name} (Code: {amfi_code})...")
        
        # Make API request
        response = requests.get(url)
        response.raise_for_status()  # Check if request was successful
        
        # Parse JSON response
        data = response.json()
        
        # Extract NAV data (list of dictionaries)
        nav_data = data.get('data', [])
        
        if nav_data:
            # Convert to DataFrame
            df = pd.DataFrame(nav_data)
            
            # Add AMFI code column
            df['amfi_code'] = amfi_code
            
            # Rename columns for consistency
            df.columns = ['date', 'nav', 'amfi_code']
            
            # Reorder columns
            df = df[['amfi_code', 'date', 'nav']]
            
            # Convert NAV to float
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # Create filename
            filename = f"live_nav_{scheme_name.replace(' ', '_').lower()}.csv"
            filepath = os.path.join(output_path, filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            
            print(f"  ✓ Saved: {filename}")
            print(f"  ✓ Records: {len(df)}")
            print(f"  ✓ Date range: {df['date'].iloc[0]} to {df['date'].iloc[-1]}\n")
        else:
            print(f"  ✗ No data found for {scheme_name}\n")
            
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error fetching {scheme_name}: {e}\n")
    except Exception as e:
        print(f"  ✗ Error processing {scheme_name}: {e}\n")

print("="*80)
print("LIVE NAV FETCHING COMPLETE")
print("="*80)