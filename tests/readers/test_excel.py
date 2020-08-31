import json
import os

import openpyxl
from openpyxl import Workbook
from openpyxl import load_workbook

from pyapacheatlas.scaffolding.templates.excel import (
    excel_template,
    ENTITYDEF_TEMPLATE
)
from pyapacheatlas.readers.excel import (
    ExcelConfiguration,
    excel_typeDefs
)

def setup_workbook(filepath, sheet_name, max_col, json_rows):
    excel_template(filepath)
    wb = load_workbook(filepath)
    active_sheet = wb[sheet_name]

    row_counter = 0
    # TODO: Make the max_col more dynamic
    for row in active_sheet.iter_rows(min_row=2, max_col=max_col, max_row= len(json_rows)+1):
        for idx, cell in enumerate(row):
            cell.value = json_rows[row_counter][idx]
        row_counter += 1
    
    wb.save(filepath)


def remove_workbook(filepath):
    if os.path.exists(filepath) and os.path.isfile(filepath):
        os.remove(filepath)


def test_excel_typeDefs_entityTypes():
    temp_filepath = "./temp_test_typeDefs_entityTYpes.xlsx"
    ec = ExcelConfiguration()
    max_cols = len(ENTITYDEF_TEMPLATE)
    # "Entity TypeName", "name", "description",
    # "isOptional", "isUnique", "defaultValue",
    # "typeName", "displayName", "valuesMinCount",
    # "valuesMaxCount", "cardinality", "includeInNotification",
    # "indexType", "isIndexable"
    json_rows = [
        ["demoType", "attrib1", "Some desc", 
        "True", "False", None,
        "string", None, None,
        None, None, None,
        None, None
        ]
    ]
    setup_workbook(temp_filepath,"EntityDefs", max_cols, json_rows )

    results = excel_typeDefs(temp_filepath, ec)

    assert("entityDefs" in results)
    assert(len(results["entityDefs"]) == 1)
    assert(results["entityDefs"][0]["attributeDefs"][0]["name"] == "attrib1")

    remove_workbook(temp_filepath)
