import json

from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.readers.excel import (
    _columns_matching_pattern,
    _parse_column_mapping, 
    _parse_table_mapping,
    ExcelConfiguration
)

def test_columns_matching_pattern():
    row = {"source attrib1":"test", "target attrib2":"results"}
    results = _columns_matching_pattern(row, "source")
    assert(len(results) == 1)
    assert(set(results) == set(["attrib1"]))

def test_columns_matching_pattern_eliminate():
    row = {"source attrib1":"test", "source data_type":"test2", "source req":"test3","target attrib2":"results"}
    results = _columns_matching_pattern(row, "source", does_not_match=["source req"])
    assert(len(results)==2)
    assert(set(results) == set(["attrib1", "data_type"]))

def test_parse_table_mapping():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)
    json_rows = [
        {
            "target table":"table1", "target type": "demo_type",
            "source table":"table0", "source type": "demo_type2",
            "process name":"proc01", "process type": "proc_type"
        }
    ]

    results = _parse_table_mapping(json_rows, excel_config, guid_tracker)

    assert(results[0].to_json(minimum = True) == {"typeName":"demo_type", "guid":-1001, "qualifiedName": "table1"})
    assert(results[1].to_json(minimum = True) == {"typeName":"demo_type2", "guid":-1002, "qualifiedName": "table0"})
    assert(results[2].to_json(minimum = True) == {"typeName":"proc_type", "guid":-1003, "qualifiedName": "proc01"})


def test_parse_table_mapping_with_attributes():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)
    json_rows = [
        {
            "target table":"table1", "target type": "demo_type","target data_type":"str",
            "source table":"table0", "source type": "demo_type2","source foo":"bar",
            "process name":"proc01", "process type": "proc_type", "process fizz":"buzz"
        }
    ]

    results = _parse_table_mapping(json_rows, excel_config, guid_tracker)

    assert(results[0].attributes["data_type"] == "str")
    assert(results[1].attributes["foo"] == "bar")
    assert(results[2].attributes["fizz"] == "buzz")


def setup_parse_column_mapping():
    json_tables = [
        {
            "target table":"table1", "target type": "demo_table",
            "source table":"table0", "source type": "demo_table",
            "process name":"proc01", "process type": "demo_process"
        }
    ]
    json_columns = [
        {
            "target column":"col1","target table": "table1",
            "source column":"col0","source table": "table0",
            "transformation":None
        }
    ]
    atlas_typedefs = [
        {"typeName":"demo_table","relationshipAttributeDefs":[{"relationshipTypeName":"demo_table_columns","name":"columns","typeName":"array<demo_column>"}]},
        {"typeName":"demo_process","relationshipAttributeDefs":[{"relationshipTypeName":"demo_process_column_lineage","name":"columnLineages","typeName":"array<demo_column_lineage>"}]}
    ]
    return json_tables, json_columns, atlas_typedefs


def test_parse_column_mapping():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)

    json_tables, json_columns, atlas_typedefs = setup_parse_column_mapping()
    
    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0].to_json()
    source_col_entity = results[1].to_json()
    col_lineage_entity = results[2].to_json()

    assert(target_col_entity["typeName"] == "demo_column")
    assert(target_col_entity["relationshipAttributes"]["table"]["typeName"] == "demo_table")
    assert(source_col_entity["typeName"] == "demo_column")
    assert(source_col_entity["relationshipAttributes"]["table"]["typeName"] == "demo_table")
    assert(col_lineage_entity["typeName"] == "demo_column_lineage")

    for entity in col_lineage_entity["attributes"]["inputs"] + col_lineage_entity["attributes"]["outputs"]:
        assert(entity["typeName"] == "demo_column")
    
    # Check that this points to the correct table process with a (default) query reference in relationshipAttribs
    proc_relationship_query_is_demo_process = False
    assert("query" in col_lineage_entity["relationshipAttributes"])
    if "query" in col_lineage_entity["relationshipAttributes"]:
        proc_relationship_query_is_demo_process = col_lineage_entity["relationshipAttributes"]["query"]["typeName"] == "demo_process"
    assert(proc_relationship_query_is_demo_process)

    
    
def test_parse_column_mapping_with_attributes():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)

    json_tables, json_columns, atlas_typedefs = setup_parse_column_mapping()

    # Update target to include an attribute
    json_columns[0].update({"target test_attrib1":"value", "target test_attrib2":"value2", "source foo":"bar"})
    
    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0]
    source_col_entity = results[1]
    col_lineage_entity = results[2]

    assert(target_col_entity.attributes["test_attrib1"] == "value")
    assert(target_col_entity.attributes["test_attrib2"] == "value2")
    assert(source_col_entity.attributes["foo"] == "bar")

def test_parse_column_mapping_with_classifications():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)

    json_tables, json_columns, atlas_typedefs = setup_parse_column_mapping()

    # Update target to include a classification
    json_columns[0].update({"target classifications":"CustomerInfo; PII", "source classifications":""})
    
    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0]
    source_col_entity = results[1]
    col_lineage_entity = results[2]

    assert(len(target_col_entity.classifications) == 2)
    assert({"typeName":"CustomerInfo","attributes":{}} in target_col_entity.classifications)
    assert({"typeName":"PII","attributes":{}} in target_col_entity.classifications)
    assert(len(source_col_entity.classifications) == 0)


def test_parse_column_mapping_with_attributes():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)

    json_tables, json_columns, atlas_typedefs = setup_parse_column_mapping()

    # Update target to include an attribute
    json_columns[0].update({"target test_attrib1":"value", "target test_attrib2":"value2", "source foo":"bar"})
    
    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0]
    source_col_entity = results[1]
    col_lineage_entity = results[2]

    assert(target_col_entity.attributes["test_attrib1"] == "value")
    assert(target_col_entity.attributes["test_attrib2"] == "value2")
    assert(source_col_entity.attributes["foo"] == "bar")

def test_parse_column_mapping_with_columnMapping():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)
    expected_obj = [
        {"ColumnMapping":[{"Source":"col0","Sink":"col1"}, {"Source":"col90","Sink":"col99"}],
        "DatasetMapping":{"Source":"table0", "Sink":"table1"}
        }
    ]
    expected = json.dumps(expected_obj)# "[{\"ColumnMapping\": [{\"Source\": \"col0\", \"Sink\": \"col1\"}], \"DatasetMapping\": {\"Source\": \"table0\", \"Sink\": \"table1\"}}]"

    json_tables, json_columns, atlas_typedefs = setup_parse_column_mapping()
    json_columns.append({
            "target column":"col99","target table": "table1",
            "source column":"col90","source table": "table0",
            "transformation":"col90 + 1"
        }
    )
    
    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs, use_column_mapping=True)

    # Demonstrating column lineage
    assert("columnMapping" in tables_and_processes[2].attributes)
    assert(tables_and_processes[2].attributes["columnMapping"] == expected)
