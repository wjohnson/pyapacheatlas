import json
import os

import openpyxl
from openpyxl import Workbook
from openpyxl import load_workbook

from pyapacheatlas.scaffolding.templates.excel import (
    excel_template,
    ENTITYDEF_TEMPLATE,
    BULKENTITY_TEMPLATE
)
from pyapacheatlas.readers.excel import (
    ExcelConfiguration,
    excel_bulkEntities,
    excel_typeDefs
)

from pyapacheatlas.scaffolding.templates.excel import _update_sheet_headers


def setup_workbook_custom_sheet(filepath, sheet_name, headers, json_rows):
    wb = Workbook()
    customSheet = wb.active
    customSheet.title = sheet_name
    _update_sheet_headers(headers, customSheet)
    row_counter = 0
    # Add the data to the sheet
    for row in customSheet.iter_rows(min_row=2, max_col=len(headers), max_row=len(json_rows)+1):
        for idx, cell in enumerate(row):
            cell.value = json_rows[row_counter][idx]
        row_counter += 1

    wb.save(filepath)
    wb.close()


def setup_workbook(filepath, sheet_name, max_col, json_rows):
    excel_template(filepath)
    wb = load_workbook(filepath)
    active_sheet = wb[sheet_name]

    row_counter = 0
    # TODO: Make the max_col more dynamic
    for row in active_sheet.iter_rows(min_row=2, max_col=max_col, max_row=len(json_rows)+1):
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
    setup_workbook(temp_filepath, "EntityDefs", max_cols, json_rows)

    results = excel_typeDefs(temp_filepath, ec)

    assert("entityDefs" in results)
    assert(len(results["entityDefs"]) == 1)
    assert(results["entityDefs"][0]["attributeDefs"][0]["name"] == "attrib1")

    remove_workbook(temp_filepath)


def test_excel_bulkEntities():
    temp_filepath = "./temp_test_excel_bulkEntities.xlsx"
    ec = ExcelConfiguration()
    max_cols = len(BULKENTITY_TEMPLATE)
    # "typeName", "name",
    # "qualifiedName", "classifications"
    json_rows = [
        ["demoType", "entityNameABC",
         "qualifiedNameofEntityNameABC", None
         ],
        ["demoType", "entityNameGHI",
         "qualifiedNameofEntityNameGHI", None
         ]
    ]
    setup_workbook(temp_filepath, "BulkEntities", max_cols, json_rows)

    results = excel_bulkEntities(temp_filepath, ec)

    try:
        assert("entities" in results)
        assert(len(results["entities"]) == 2)
    finally:
        remove_workbook(temp_filepath)


def test_excel_bulkEntities_withClassifications():
    temp_filepath = "./temp_test_excel_bulkEntitiesWithClassifications.xlsx"
    ec = ExcelConfiguration()
    max_cols = len(BULKENTITY_TEMPLATE)
    # "typeName", "name",
    # "qualifiedName", "classifications"
    json_rows = [
        ["demoType", "entityNameABC",
         "qualifiedNameofEntityNameABC", "PII"
         ],
        ["demoType", "entityNameGHI",
         "qualifiedNameofEntityNameGHI", "PII;CLASS2"
         ]
    ]

    setup_workbook(temp_filepath, "BulkEntities", max_cols, json_rows)

    results = excel_bulkEntities(temp_filepath, ec)

    try:
        assert("entities" in results)
        assert(len(results["entities"]) == 2)
        abc = results["entities"][0]
        ghi = results["entities"][1]

        assert(len(abc["classifications"]) == 1)
        assert(len(ghi["classifications"]) == 2)

        assert(abc["classifications"][0]["typeName"] == "PII")
        ghi_classification_types = set(
            [x["typeName"] for x in ghi["classifications"]]
        )
        assert(set(["PII", "CLASS2"]) == ghi_classification_types)
    finally:
        remove_workbook(temp_filepath)


def test_excel_bulkEntities_dynamicAttributes():
    temp_filepath = "./temp_test_excel_bulkEntitieswithAttributes.xlsx"
    ec = ExcelConfiguration()

    headers = BULKENTITY_TEMPLATE + ["attrib1", "attrib2"]
    # "typeName", "name",
    # "qualifiedName", "classifications"
    # "attrib1", "attrib2"
    json_rows = [
        ["demoType", "entityNameABC",
         "qualifiedNameofEntityNameABC", None,
         None, "abc"
         ],
        ["demoType", "entityNameGHI",
         "qualifiedNameofEntityNameGHI", None,
         "ghi", "abc2"
         ]
    ]

    setup_workbook_custom_sheet(
        temp_filepath, "BulkEntities", headers, json_rows)

    results = excel_bulkEntities(temp_filepath, ec)

    try:
        assert("entities" in results)
        assert(len(results["entities"]) == 2)
        abc = results["entities"][0]
        ghi = results["entities"][1]

        assert("attrib1" not in abc["attributes"])
        assert("attrib2" in abc["attributes"])
        assert(abc["attributes"]["attrib2"] == "abc")

        assert("attrib1" in ghi["attributes"])
        assert("attrib2" in ghi["attributes"])
        assert(ghi["attributes"]["attrib2"] == "abc2")
        assert(ghi["attributes"]["attrib1"] == "ghi")

    finally:
        remove_workbook(temp_filepath)
