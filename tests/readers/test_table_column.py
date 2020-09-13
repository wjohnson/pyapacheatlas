import json

from pyapacheatlas.core import AtlasProcess
from pyapacheatlas.readers.util import *

from pyapacheatlas.readers.reader import Reader, ReaderConfiguration

# Set up some cross-test objects and functions
READER_CONFIG = ReaderConfiguration()


def setup_column_lineage_entities():
    json_tables = [
        {
            "Target Table": "table1", "Target Type": "demo_table",
            "Source Table": "table0", "Source Type": "demo_table",
            "Process Name": "proc01", "Process Type": "demo_process"
        }
    ]

    json_columns = [
        {
            "Target Column": "col1", "Target Table": "table1",
            "Source Column": "col0", "Source Table": "table0",
            "Transformation": None
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
            "Target Table": "table1", "Target Type": "demo_type",
            "Source Table": "table0", "Source Type": "demo_type2",
            "Process Name": "proc01", "Process Type": "proc_type"
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
            "Target Table": "table1", "Target Type": "demo_type",
            "Target data_type": "str", "Source Table": "table0",
            "Source Type": "demo_type2", "Source foo": "bar",
            "Process Name": "proc01", "Process Type": "proc_type",
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
            "Target Table": "table1", "Target Type": "demo_type",
            "Source Table": "table0", "Source Type": "demo_type",
            "Process Name": "proc01", "Process Type": "proc_type"
        },
        {
            "Target Table": "table1", "Target Type": "demo_type",
            "Source Table": "tableB", "Source Type": "demo_type",
            "Process Name": "proc01", "Process Type": "proc_type"
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
        {"Target Classifications": "CustomerInfo; PII", "Source Classifications": ""})

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
        "Target Column": "col99", "Target Table": "table1",
        "Source Column": "col90", "Source Table": "table0",
        "Transformation": "col90 + 1"
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
            "Target Table": "table1", "Target Type": "demo_table",
            "Source Table": "tableB", "Source Type": "demo_table",
            "Process Name": "proc01", "Process Type": "demo_process"
        }
    )
    json_columns[0].update({"Transformation": "colB + col0"})
    # Adding in an extra column
    json_columns.append(
        {
            "Target Column": "col1", "Target Table": "table1",
            "Source Column": "colB", "Source Table": "tableB",
            "Transformation": "colB + col0"
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
