#!/usr/bin/env python3
"""
OCS Catalogue Data Analysis Script
Analyzes the structure and content of the OCS Excel catalogue file
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import json
from typing import Dict, List, Any

def analyze_excel_structure(file_path: str) -> Dict[str, Any]:
    """Analyze the structure of the OCS Excel file"""
    try:
        # Load Excel file
        print(f"Loading Excel file: {file_path}")
        
        # Get all sheet names
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        print(f"Found {len(sheet_names)} sheets: {sheet_names}")
        
        analysis = {
            "file_path": file_path,
            "sheet_names": sheet_names,
            "sheets": {}
        }
        
        # Analyze each sheet
        for sheet_name in sheet_names:
            print(f"\nAnalyzing sheet: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            sheet_info = {
                "shape": df.shape,
                "columns": list(df.columns),
                "dtypes": df.dtypes.to_dict(),
                "null_counts": df.isnull().sum().to_dict(),
                "sample_data": df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
            # Get unique values for categorical columns
            categorical_cols = df.select_dtypes(include=['object']).columns
            unique_values = {}
            for col in categorical_cols:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 20:  # Only show if manageable number
                    unique_values[col] = unique_vals.tolist()
                else:
                    unique_values[col] = f"Too many values ({len(unique_vals)})"
            
            sheet_info["unique_values"] = unique_values
            
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Column names: {list(df.columns)}")
            
            analysis["sheets"][sheet_name] = sheet_info
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing Excel file: {e}")
        return {"error": str(e)}

def extract_product_schema(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the product schema from the analysis"""
    if "error" in analysis:
        return {"error": analysis["error"]}
    
    # Find the main product sheet (usually the first or largest one)
    main_sheet = None
    max_rows = 0
    
    for sheet_name, sheet_info in analysis["sheets"].items():
        if sheet_info["shape"][0] > max_rows:
            max_rows = sheet_info["shape"][0]
            main_sheet = sheet_name
    
    if not main_sheet:
        return {"error": "No valid product sheet found"}
    
    main_sheet_info = analysis["sheets"][main_sheet]
    
    # Map columns to standard product fields
    column_mapping = {}
    columns = main_sheet_info["columns"]
    
    # Common cannabis product fields mapping
    field_patterns = {
        "product_id": ["id", "product_id", "sku", "product_sku"],
        "name": ["name", "product_name", "title", "product_title"],
        "brand": ["brand", "manufacturer", "producer", "brand_name"],
        "category": ["category", "product_category", "type", "product_type"],
        "subcategory": ["subcategory", "sub_category", "subtype"],
        "thc_content": ["thc", "thc_content", "thc_percentage", "thc_%"],
        "cbd_content": ["cbd", "cbd_content", "cbd_percentage", "cbd_%"],
        "price": ["price", "unit_price", "cost", "retail_price"],
        "weight": ["weight", "size", "quantity", "net_weight"],
        "description": ["description", "product_description", "details"],
        "strain_type": ["strain", "strain_type", "indica_sativa"],
        "effects": ["effects", "effect", "benefits"],
        "flavors": ["flavors", "flavor", "taste", "terpenes"],
        "availability": ["available", "in_stock", "status"],
        "image_url": ["image", "image_url", "photo", "picture"],
        "vendor_id": ["vendor", "vendor_id", "supplier", "supplier_id"]
    }
    
    for field, patterns in field_patterns.items():
        for col in columns:
            col_lower = col.lower().replace(" ", "_").replace("-", "_")
            if any(pattern in col_lower for pattern in patterns):
                column_mapping[field] = col
                break
    
    schema = {
        "main_sheet": main_sheet,
        "total_products": max_rows,
        "column_mapping": column_mapping,
        "all_columns": columns,
        "sample_data": main_sheet_info["sample_data"][:2],  # Show first 2 records
        "data_types": main_sheet_info["dtypes"]
    }
    
    return schema

def main():
    """Main function"""
    data_file = Path(__file__).parent.parent / "data" / "datasets" / "OCS_Catalogue_31_Jul_2025_226PM.xlsx"
    
    if not data_file.exists():
        print(f"Error: Data file not found at {data_file}")
        sys.exit(1)
    
    print("=== OCS Catalogue Data Analysis ===\n")
    
    # Analyze Excel structure
    analysis = analyze_excel_structure(str(data_file))
    
    if "error" in analysis:
        print(f"Analysis failed: {analysis['error']}")
        sys.exit(1)
    
    # Extract product schema
    schema = extract_product_schema(analysis)
    
    if "error" in schema:
        print(f"Schema extraction failed: {schema['error']}")
        sys.exit(1)
    
    # Save analysis results
    output_dir = Path(__file__).parent.parent / "data" / "pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "ocs_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2, default=str)
    
    with open(output_dir / "product_schema.json", "w") as f:
        json.dump(schema, f, indent=2, default=str)
    
    # Print summary
    print("\n=== Analysis Summary ===")
    print(f"Main product sheet: {schema['main_sheet']}")
    print(f"Total products: {schema['total_products']}")
    print(f"Columns found: {len(schema['all_columns'])}")
    print(f"Mapped fields: {len(schema['column_mapping'])}")
    
    print("\n=== Column Mapping ===")
    for field, column in schema['column_mapping'].items():
        print(f"  {field}: {column}")
    
    print("\n=== Unmapped Columns ===")
    mapped_columns = set(schema['column_mapping'].values())
    unmapped = [col for col in schema['all_columns'] if col not in mapped_columns]
    for col in unmapped:
        print(f"  {col}")
    
    if schema['sample_data']:
        print("\n=== Sample Data (First Product) ===")
        sample = schema['sample_data'][0]
        for key, value in sample.items():
            if pd.notna(value):
                print(f"  {key}: {value}")
    
    print(f"\nAnalysis complete! Results saved to:")
    print(f"  - {output_dir / 'ocs_analysis.json'}")
    print(f"  - {output_dir / 'product_schema.json'}")

if __name__ == "__main__":
    main()