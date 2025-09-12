import pandas as pd
import re

def generate_slug(brand, product_name, sub_category, size):
    """Generate a URL-friendly slug from brand, product name, sub-category, and size."""
    parts = []
    
    # Add brand if available
    if brand and pd.notna(brand):
        brand_slug = str(brand).lower()
        brand_slug = re.sub(r'[^\w\s-]', '', brand_slug)
        brand_slug = re.sub(r'[-\s]+', '-', brand_slug).strip('-')
        if brand_slug:
            parts.append(brand_slug)
    
    # Add product name if available
    if product_name and pd.notna(product_name):
        name_slug = str(product_name).lower()
        name_slug = re.sub(r'[^\w\s-]', '', name_slug)
        name_slug = re.sub(r'[-\s]+', '-', name_slug).strip('-')
        if name_slug:
            parts.append(name_slug)
    
    # Add sub-category if available
    if sub_category and pd.notna(sub_category):
        sub_cat_slug = str(sub_category).lower()
        sub_cat_slug = re.sub(r'[^\w\s-]', '', sub_cat_slug)
        sub_cat_slug = re.sub(r'[-\s]+', '-', sub_cat_slug).strip('-')
        if sub_cat_slug:
            parts.append(sub_cat_slug)
    
    # Add size if available
    if size and pd.notna(size):
        size_slug = str(size).lower()
        size_slug = re.sub(r'[^\w\s-]', '', size_slug)
        size_slug = re.sub(r'[-\s]+', '-', size_slug).strip('-')
        if size_slug:
            parts.append(size_slug)
    
    # Join all parts with hyphen
    slug = '-'.join(parts) if parts else 'product'
    return slug

# Read the Excel file
file_path = '/Users/charrcy/Downloads/OCS_Catalogue_31_Jul_2025_957PM.xlsx'
df = pd.read_excel(file_path)

# Generate slugs for each row
df['generated_slug'] = df.apply(lambda row: generate_slug(
    row.get('Brand'),
    row.get('Product Name'),
    row.get('Sub-Category'),
    row.get('Size')
), axis=1)

# Find duplicate slugs
duplicate_slugs = df[df.duplicated('generated_slug', keep=False)]

print(f"Total rows: {len(df)}")
print(f"Rows with duplicate slugs: {len(duplicate_slugs)}")
print(f"Unique slugs: {df['generated_slug'].nunique()}")

# Show examples of duplicate slugs with the specific rows that violate
error_rows = [368, 380, 381, 429, 431, 494, 553, 573, 575, 581]
print(f"\n\nExamples of duplicate slugs (first 10 error rows):")
for row_idx in error_rows[:10]:
    if row_idx < len(df):
        row = df.iloc[row_idx]
        slug = row['generated_slug']
        print(f"\nRow {row_idx}:")
        print(f"  Brand: {row['Brand']}")
        print(f"  Product: {row['Product Name']}")
        print(f"  Sub-Category: {row['Sub-Category']}")
        print(f"  Size: {row['Size']}")
        print(f"  Generated slug: {slug}")
        print(f"  OCS Variant: {row['OCS Variant Number']}")
        
        # Find all rows with the same slug
        same_slug = df[df['generated_slug'] == slug]
        if len(same_slug) > 1:
            print(f"  DUPLICATE! Found {len(same_slug)} rows with same slug:")
            for idx, dup_row in same_slug.iterrows():
                print(f"    Row {idx}: OCS Variant {dup_row['OCS Variant Number']}")