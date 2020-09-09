import json
import sys

from pyapacheatlas.readers import ExcelConfiguration, ExcelReader
from pyapacheatlas.core.whatif import WhatIfValidator

if __name__ == "__main__":
    """
    Demonstrate how you would read in an excel file and an existing atlas
    type definition json (e.g. contains {"entityDefs":[...],...}) and 
    produces the batch of results and provides the what if validation.
    """
    if len(sys.argv) != 3:
        raise ValueError(
            "ERROR: There should be an excel_file_path and type_def_path provided on the CLI")
    excel_path = sys.argv[1]
    if excel_path is None:
        raise ValueError(
            "No excel file path was provided on the command line.")
    json_path = sys.argv[2]
    if json_path is None:
        raise ValueError(
            "No type definition file path was provided on the command line.")

    with open(json_path, 'r') as fp:
        type_defs = json.load(fp)

    excel_config = ExcelConfiguration()
    excel_reader = ExcelReader(excel_config)
    whatif = WhatIfValidator(type_defs=type_defs)

    results = excel_reader.parse_lineages(
        excel_path,
        type_defs,
        use_column_mapping=True
    )

    report = whatif.validate_entities(results)

    print("===REPORT===")
    print(json.dumps(report, indent=2))

    print("===EXCEL RESULTS===")
    print(json.dumps(results, indent=2))
