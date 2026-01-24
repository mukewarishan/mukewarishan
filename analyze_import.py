import pandas as pd
import openpyxl

# Read the Excel file
file_path = '/tmp/import_data.xlsx'

# Try reading with pandas
print("=" * 50)
print("Reading with pandas:")
print("=" * 50)
df = pd.read_excel(file_path)
print(f"\nTotal rows: {len(df)}")
print(f"\nColumn names:\n{list(df.columns)}")
print(f"\nFirst 3 rows:")
print(df.head(3).to_string())

# Check for any datetime columns
print("\n" + "=" * 50)
print("Column data types:")
print("=" * 50)
print(df.dtypes)

# Show some statistics
print("\n" + "=" * 50)
print("Non-null counts:")
print("=" * 50)
print(df.count())
