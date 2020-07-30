import json
import os

# PyApacheAtlas packages
from pyapacheatlas.scaffolding import column_lineage_scaffold # Create dummy types
from pyapacheatlas.scaffolding.templates import excel_template # Create the excel template file to be populated

if __name__ == "__main__":
    # Create the demo scaffolding
    print("Creating the scaffolding json file")
    scaffold = column_lineage_scaffold("demo")
    with open("./demo_scaffold.json", 'w') as fp:
        fp.write(
            json.dumps(scaffold, indent=1)
        )
    
    # Create the excel template file
    print("Creating the excel template file")
    excel_template("./demo_excel_template.xlsx")
