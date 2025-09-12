import pandas as pd

# Read the Excel file
file_path = '/Users/charrcy/Downloads/OCS_Catalogue_31_Jul_2025_957PM.xlsx'
df = pd.read_excel(file_path, nrows=5)

# Print all column names
print("Excel columns:")
for i, col in enumerate(df.columns):
    print(f"{i+1}. '{col}'")

print(f"\nTotal columns: {len(df.columns)}")

# Check for Brand column specifically
if 'Brand' in df.columns:
    print(f"\nBrand column exists")
    print(f"Sample Brand values: {df['Brand'].head().tolist()}")
else:
    print("\nBrand column NOT found")
    # Check for similar column names
    brand_like = [col for col in df.columns if 'brand' in col.lower()]
    if brand_like:
        print(f"Similar columns: {brand_like}")