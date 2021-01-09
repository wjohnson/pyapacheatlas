import json

import pytest

from pyapacheatlas.core import AtlasProcess
from pyapacheatlas.readers.util import *

from pyapacheatlas.readers.reader import Reader, ReaderConfiguration

# Set up some cross-test objects and functions
READER_CONFIG = ReaderConfiguration()


def setup_column_lineage_entities():
    json_tables = [
        {
            "Target table": "table1", "Target type": "demo_table",
            "Source table": "table0", "Source type": "demo_table",
            "Process name": "proc01", "Process type": "demo_process"
        }
    ]

    json_columns = [
        {
            "Target column": "col1", "Target table": "table1",
            "Source column": "col0", "Source table": "table0",
            "transformation": None
        }
    ]

    atlas_typedefs = {"entityDefs": [
        {"typeName": "demo_table", "relationshipAttributeDefs": [
            {"relationshipTypeName": "demo_table_columns", "name": "columns",
             "typeName": "array<demo_column>"}]},
        {"typeName": "demo_process", "relationshipAttributeDefs": [
            {"relationshipTypeName": "demo_process_column_lineage",
             "name": "columnLineages",
             "typeName": "array<demo_column_lineage>"}]}
    ],
        "relationshipDefs": [
        {"name": "demo_table_columns",
         "endDef1": {"type": "demo_table", "name": "columns"},
         "endDef2": {"type": "demo_column", "name": "table"}
         },
        {"name": "demo_process_column_lineage",
         "endDef1": {"type": "demo_column_lineage", "name": "query"},
         "endDef2": {"type": "demo_process", "name": "columnLineages"}
         }
    ]
    }
    return json_tables, json_columns, atlas_typedefs


# Begin actual tests
def test_table_lineage():
    reader = Reader(READER_CONFIG)
    json_rows = [
        {
            "Target table": "table1", "Target type": "demo_type",
            "Source table": "table0", "Source type": "demo_type2",
            "Process name": "proc01", "Process type": "proc_type"
        }
    ]

    results = reader.parse_table_lineage(json_rows)

    assert(results[0].to_json(minimum=True) == {
           "typeName": "demo_type", "guid": -1001, "qualifiedName": "table1"})
    assert(results[1].to_json(minimum=True) == {
           "typeName": "demo_type2", "guid": -1002, "qualifiedName": "table0"})
    assert(results[2].to_json(minimum=True) == {
           "typeName": "proc_type", "guid": -1003, "qualifiedName": "proc01"})


def test_table_lineage_with_attributes():
    reader = Reader(READER_CONFIG)
    json_rows = [
        {
            "Target table": "table1", "Target type": "demo_type",
            "Target data_type": "str", "Source table": "table0",
            "Source type": "demo_type2", "Source foo": "bar",
            "Process name": "proc01", "Process type": "proc_type",
            "Process fizz": "buzz"
        }
    ]

    results = reader.parse_table_lineage(json_rows)

    assert(results[0].attributes["data_type"] == "str")
    assert(results[1].attributes["foo"] == "bar")
    assert(results[2].attributes["fizz"] == "buzz")


def test_table_lineage_multiple_inputs():
    reader = Reader(READER_CONFIG)
    json_tables = [
        {
            "Target table": "table1", "Target type": "demo_type",
            "Source table": "table0", "Source type": "demo_type",
            "Process name": "proc01", "Process type": "proc_type"
        },
        {
            "Target table": "table1", "Target type": "demo_type",
            "Source table": "tableB", "Source type": "demo_type",
            "Process name": "proc01", "Process type": "proc_type"
        }
    ]

    results = reader.parse_table_lineage(json_rows=json_tables)

    assert(len(results) == 4)
    assert(results[3].to_json(minimum=True) == {
           "typeName": "proc_type", "guid": -1003, "qualifiedName": "proc01"})
    process_inputs_qualified_names = [
        p["qualifiedName"] for p in results[3].get_inputs()]
    process_outputs_qualified_names = [
        p["qualifiedName"] for p in results[3].get_outputs()]
    assert(len(process_inputs_qualified_names) == 2)
    assert(len(process_outputs_qualified_names) == 1)

    assert(set(process_inputs_qualified_names) == set(["table0", "tableB"]))
    assert(set(process_outputs_qualified_names) == set(["table1"]))


def test_column_lineage_entities():
    reader = Reader(READER_CONFIG)

    json_tables, json_columns, atlas_typedefs = setup_column_lineage_entities()

    # Outputs -1003 as the last guid
    tables_and_processes = reader.parse_table_lineage(json_tables)

    results = reader.parse_column_lineage(
        json_columns, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0].to_json()
    source_col_entity = results[1].to_json()
    col_lineage_entity = results[2].to_json()

    assert(target_col_entity["typeName"] == "demo_column")
    assert(target_col_entity["relationshipAttributes"]
           ["table"]["typeName"] == "demo_table")
    assert(source_col_entity["typeName"] == "demo_column")
    assert(source_col_entity["relationshipAttributes"]
           ["table"]["typeName"] == "demo_table")
    assert(col_lineage_entity["typeName"] == "demo_column_lineage")

    for entity in col_lineage_entity["attributes"]["inputs"] + col_lineage_entity["attributes"]["outputs"]:
        assert(entity["typeName"] == "demo_column")

    # Check that this points to the correct table process with a (default) query reference in relationshipAttribs
    proc_relationship_query_is_demo_process = False
    assert("query" in col_lineage_entity["relationshipAttributes"])
    if "query" in col_lineage_entity["relationshipAttributes"]:
        proc_relationship_query_is_demo_process = col_lineage_entity[
            "relationshipAttributes"]["query"]["typeName"] == "demo_process"
    assert(proc_relationship_query_is_demo_process)


def test_column_lineage_entities_with_attributes():
    reader = Reader(READER_CONFIG)

    json_tables, json_columns, atlas_typedefs = setup_column_lineage_entities()

    # Update target to include an attribute
    json_columns[0].update({"Target test_attrib1": "value",
                            "Target test_attrib2": "value2", "Source foo": "bar"})

    # Outputs -1003 as the last guid
    tables_and_processes = reader.parse_table_lineage(json_tables)

    results = reader.parse_column_lineage(
        json_columns, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0]
    source_col_entity = results[1]
    col_lineage_entity = results[2]

    assert(target_col_entity.attributes["test_attrib1"] == "value")
    assert(target_col_entity.attributes["test_attrib2"] == "value2")
    assert(source_col_entity.attributes["foo"] == "bar")


def test_column_lineage_entities_with_classifications():
    reader = Reader(READER_CONFIG)

    json_tables, json_columns, atlas_typedefs = setup_column_lineage_entities()

    # Update target to include a classification
    json_columns[0].update(
        {"Target classifications": "CustomerInfo; PII", "Source classifications": ""})

    # Outputs -1003 as the last guid
    tables_and_processes = reader.parse_table_lineage(json_tables)

    results = reader.parse_column_lineage(
        json_columns, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0]
    source_col_entity = results[1]
    col_lineage_entity = results[2]

    assert(len(target_col_entity.classifications) == 2)
    assert({"typeName": "CustomerInfo", "attributes": {}}
           in target_col_entity.classifications)
    assert({"typeName": "PII", "attributes": {}}
           in target_col_entity.classifications)
    assert(len(source_col_entity.classifications) == 0)


def test_column_lineage_entities_with_columnMapping():
    reader = Reader(READER_CONFIG)
    expected_obj = [
        {"ColumnMapping": [{"Source": "col0", "Sink": "col1"}, {"Source": "col90", "Sink": "col99"}],
         "DatasetMapping": {"Source": "table0", "Sink": "table1"}
         }
    ]
    # "[{\"ColumnMapping\": [{\"Source\": \"col0\", \"Sink\": \"col1\"}], \"DatasetMapping\": {\"Source\": \"table0\", \"Sink\": \"table1\"}}]"
    expected = json.dumps(expected_obj)

    json_tables, json_columns, atlas_typedefs = setup_column_lineage_entities()

    json_columns.append({
        "Target column": "col99", "Target table": "table1",
        "Source column": "col90", "Source table": "table0",
        "transformation": "col90 + 1"
    }
    )

    # Outputs -1003 as the last guid
    tables_and_processes = reader.parse_table_lineage(json_tables)

    results = reader.parse_column_lineage(
        json_columns, tables_and_processes, atlas_typedefs, use_column_mapping=True)

    # Demonstrating column lineage
    assert("columnMapping" in tables_and_processes[2].attributes)
    assert(tables_and_processes[2].attributes["columnMapping"] == expected)


def test_column_lineage_entities_when_multi_tabled_inputs():
    reader = Reader(READER_CONFIG)
    json_tables, json_columns, atlas_typedefs = setup_column_lineage_entities()
    # Adding in an extra table
    json_tables.append(
        {
            "Target table": "table1", "Target type": "demo_table",
            "Source table": "tableB", "Source type": "demo_table",
            "Process name": "proc01", "Process type": "demo_process"
        }
    )
    json_columns[0].update({"transformation": "colB + col0"})
    # Adding in an extra column
    json_columns.append(
        {
            "Target column": "col1", "Target table": "table1",
            "Source column": "colB", "Source table": "tableB",
            "transformation": "colB + col0"
        }
    )
    expected_col_map_obj = [
        {"ColumnMapping": [{"Source": "col0", "Sink": "col1"}],
         "DatasetMapping": {"Source": "table0", "Sink": "table1"}
         },
        {"ColumnMapping": [{"Source": "colB", "Sink": "col1"}],
         "DatasetMapping": {"Source": "tableB", "Sink": "table1"}
         }
    ]

    table_entities = reader.parse_table_lineage(json_tables)
    column_entities = reader.parse_column_lineage(
        json_columns, table_entities, atlas_typedefs, use_column_mapping=True)

    # Three columns and one process entity
    assert(len(column_entities) == 4)
    process_entities = [
        e for e in column_entities if isinstance(e, AtlasProcess)]
    assert(len(process_entities) == 1)
    process_entity = process_entities[0]

    process_inputs_qualified_names = [p["qualifiedName"]
                                      for p in process_entity.get_inputs()]
    process_outputs_qualified_names = [
        p["qualifiedName"] for p in process_entity.get_outputs()]
    assert(len(process_inputs_qualified_names) == 2)
    assert(len(process_outputs_qualified_names) == 1)

    assert(set(process_inputs_qualified_names) ==
           set(["table0#col0", "tableB#colB"]))
    assert(set(process_outputs_qualified_names) == set(["table1#col1"]))

    table_process_entities = [
        e for e in table_entities if isinstance(e, AtlasProcess)]
    table_process_entity = table_process_entities[0]
    # Should now contain the expected column Mappings
    assert("columnMapping" in table_process_entity.attributes)
    resulting_colmap = json.loads(
        table_process_entity.attributes["columnMapping"])
    assert(len(expected_col_map_obj) == len(resulting_colmap))
    assert(all([res in expected_col_map_obj for res in resulting_colmap]))


def test_parse_update_lineage():
    reader = Reader(READER_CONFIG)
    json_rows = [
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget02",
         "Source typeName": None, "Source qualifiedName": None,
         "Process name": "proc02", "Process qualifiedName": "procqual02",
         "Process typeName": "Process3"
         },
        {"Target typeName": None, "Target qualifiedName": None,
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource03",
         "Process name": "proc03", "Process qualifiedName": "procqual03",
         "Process typeName": "Process4"
         },
        {"Target typeName": "N/A", "Target qualifiedName": "N/A",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource03",
         "Process name": "proc04", "Process qualifiedName": "procqual04",
         "Process typeName": "Process5"
         }
    ]

    results = reader.parse_update_lineage(json_rows)

    assert(len(results) == 4)
    full_update = results[0]
    target_update = results[1]
    source_update = results[2]
    target_destroy = results[3]

    assert(full_update["typeName"] == "Process2")
    assert(full_update["attributes"]["name"] == "proc01")
    assert(len(full_update["attributes"]["inputs"]) == 1)
    assert(len(full_update["attributes"]["outputs"]) == 1)

    fullupd_input = full_update["attributes"]["inputs"][0]
    fullupd_output = full_update["attributes"]["outputs"][0]

    assert(fullupd_input == {"typeName": "demo_table2",
                             "uniqueAttributes": {"qualifiedName": "demosource"}})
    assert(fullupd_output == {"typeName": "demo_table",
                              "uniqueAttributes": {"qualifiedName": "demotarget"}})

    # For a partial update, inputs will be set to None
    assert(target_update["attributes"]["inputs"] == None)

    # For a partial update, outputs will be set to None
    assert(source_update["attributes"]["outputs"] == None)

    # If they use the "N/A" keyword in qualifiedName, destroy that type
    assert(target_destroy["attributes"]["outputs"] == [])
    assert(target_destroy["attributes"]["inputs"] == [
        {"typeName": "demo_table2",
         "uniqueAttributes": {"qualifiedName": "demosource03"}}])


def test_parse_update_lineage_multi_in():
    reader = Reader(READER_CONFIG)
    json_rows = [
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
        {"Target typeName": None, "Target qualifiedName": None,
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource2",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         }
    ]

    results = reader.parse_update_lineage(json_rows)

    assert(len(results) == 1)
    inputs = results[0]["attributes"]["inputs"]
    outputs = results[0]["attributes"]["outputs"]
    assert(len(inputs) == 2)
    input_names = set([x["uniqueAttributes"]["qualifiedName"] for x in inputs])
    assert(input_names == set(["demosource", "demosource2"]))
    assert(len(outputs) == 1)


def test_parse_update_lineage_multi_out():

    reader = Reader(READER_CONFIG)

    json_rows = [
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget2",
         "Source typeName": None, "Source qualifiedName": None,
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         }
    ]

    results = reader.parse_update_lineage(json_rows)

    assert(len(results) == 1)
    inputs = results[0]["attributes"]["inputs"]
    outputs = results[0]["attributes"]["outputs"]
    assert(len(outputs) == 2)
    output_names = set([x["uniqueAttributes"]["qualifiedName"]
                        for x in outputs])
    assert(output_names == set(["demotarget", "demotarget2"]))
    assert(len(inputs) == 1)


def test_parse_update_lineage_multi_dedupe():

    reader = Reader(READER_CONFIG)

    json_rows = [
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
    ]

    with pytest.warns(UserWarning):
        results = reader.parse_update_lineage(json_rows)
    assert(len(results) == 1)
    inputs = results[0]["attributes"]["inputs"]
    outputs = results[0]["attributes"]["outputs"]
    assert(len(outputs) == 1)
    assert(len(inputs) == 1)


def test_parse_update_lineage_multi_row_with_na_last():

    reader = Reader(READER_CONFIG)

    json_rows = [

        {"Target typeName": "demo_table", "Target qualifiedName": "demotarget",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
        {"Target typeName": "N/A", "Target qualifiedName": "N/A",
         "Source typeName": "demo_table2", "Source qualifiedName": "demosource2",
         "Process name": "proc01", "Process qualifiedName": "procqual01",
         "Process typeName": "Process2"
         },
    ]
    with pytest.warns(UserWarning):
        results = reader.parse_update_lineage(json_rows)
    assert(len(results) == 1)
    inputs = results[0]["attributes"]["inputs"]
    outputs = results[0]["attributes"]["outputs"]
    assert(len(outputs) == 0)
    assert(len(inputs) == 2)
