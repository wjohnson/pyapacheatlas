import json
import os
import sys

# PyApacheAtlas packages
from pyapacheatlas.scaffolding import column_lineage_scaffold # Create dummy types
from pyapacheatlas.scaffolding.templates import excel_template # Create the excel template file to be populated

if __name__ == "__main__":
    """
    Generates the demo scaffolding and excel template file.
    """
    if len(sys.argv) == 2:
        column_map_switch = True if "YES".startswith(sys.argv[1].upper()) else False
        print("INFO: Using column mapping on the table lineage processes")
    else:
        column_map_switch = False
        print("INFO: NOT using column mapping on the table lineage processes")
    
    # Create the demo scaffolding
    print("Creating the scaffolding json file")
    scaffold = column_lineage_scaffold("demo", use_column_mapping=column_map_switch)
    with open("./demo_scaffold.json", 'w') as fp:
        fp.write(
            json.dumps(scaffold, indent=1)
        )
    
    # Create the excel template file
    print("Creating the excel template file")
    excel_template("./demo_excel_template.xlsx")
