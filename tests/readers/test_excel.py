from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.readers.excel import ExcelConfiguration, _parse_column_mapping, _parse_table_mapping

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


def test_parse_column_mapping():
    excel_config = ExcelConfiguration()
    guid_tracker = GuidTracker(-1000)
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

    atlas_typedefs = {
        "entityDefs":[
            {"typeName":"demo_table","relationshipAttributes":[{"relationshipTypeName":"demo_table_columns","name":"columns","typeName":"array<demo_column>"}]},
            {"typeName":"demo_process","relationshipAttributes":[{"relationshipTypeName":"demo_process_column_lineage","name":"columnLineages","typeName":"array<demo_column_lineage>"}]}
        ]
    }

    # Outputs -1003 as the last guid
    tables_and_processes = _parse_table_mapping(json_tables, excel_config, guid_tracker)

    results = _parse_column_mapping(json_columns, excel_config, guid_tracker, tables_and_processes, atlas_typedefs)

    # Two column entities
    # One process entity
    target_col_entity = results[0].to_json()
    source_col_entity = results[1].to_json()
    col_lineage_entity = results[2].to_json()

    assert(target_col_entity["typeName"] == "demo_column")
    assert(source_col_entity["typeName"] == "demo_column")
    assert(col_lineage_entity["typeName"] == "demo_column_lineage")

    for entity in col_lineage_entity["attributes"]["inputs"] + col_lineage_entity["attributes"]["output"]:
        assert(entity["typeName" == "demo_column"])
    
    proc_relationship_query_is_demo_process = False
    if "query" in col_lineage_entity["relationshipAttributes"]:
        proc_relationship_query_is_demo_process = col_lineage_entity["relationshipAttributes"]["query"]["typeName"] == "demo_process"

    assert(proc_relationship_query_is_demo_process)

    