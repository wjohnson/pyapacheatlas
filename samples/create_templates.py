import argparse
import json
import os
import sys

# PyApacheAtlas packages
from pyapacheatlas.scaffolding import column_lineage_scaffold  # Create dummy types
# Create the excel template file to be populated
from pyapacheatlas.readers import ExcelReader

if __name__ == "__main__":
    """
    Generates the demo scaffolding and excel template file.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-column-mapping", action="store_true",
        help="Use column-mapping attributes for Azure Data Catalog visualizations."
    )
    parser.add_argument("--prefix", help="The prefix for the table and columns lineage types.")
    args = parser.parse_args()

    # Create the demo scaffolding
    print("Creating the scaffolding json file")
    scaffold = column_lineage_scaffold(
        args.prefix, 
        use_column_mapping=args.use_column_mapping
    )
    
    with open(f"./{args.prefix}_scaffold.json", 'w') as fp:
        fp.write(
            json.dumps(scaffold, indent=1)
    )

    # Create the excel template file
    print("Creating the excel template file")
    ExcelReader.make_template(f"./{args.prefix}_excel_template.xlsx")
