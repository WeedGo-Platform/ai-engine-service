import pandas as pd

# Read the Excel file
file_path = '/Users/charrcy/Downloads/OCS_Catalogue_31_Jul_2025_957PM.xlsx'
df = pd.read_excel(file_path)

# Check for duplicates based on brand-productname-subcategory-size
df['check_key'] = (
    df['Brand'].fillna('').astype(str) + '-' +
    df['Product Name'].fillna('').astype(str) + '-' +
    df['Sub-Category'].fillna('').astype(str) + '-' +
    df['Size'].fillna('').astype(str)
)

# Find duplicates
duplicates = df[df.duplicated('check_key', keep=False)]
print(f"Total rows: {len(df)}")
print(f"Duplicate rows: {len(duplicates)}")
print(f"Unique combinations: {df['check_key'].nunique()}")

# Show some examples of duplicates
if len(duplicates) > 0:
    print("\nExample duplicates (first 10):")
    for key, group in duplicates.groupby('check_key').head(10):
        if len(group) > 1:
            print(f"\nKey: {key}")
            print(f"  Rows: {group.index.tolist()}")
            print(f"  OCS Variants: {group['OCS Variant Number'].tolist()}")
            break  # Just show one example

# Check what makes them unique
print("\n\nChecking uniqueness with OCS Variant Number:")
df['unique_key'] = df['check_key'] + '-' + df['OCS Variant Number'].astype(str)
print(f"Unique with OCS Variant: {df['unique_key'].nunique()}")
print(f"Expected total: {len(df)}")