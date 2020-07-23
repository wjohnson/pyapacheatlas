from pyapacheatlas.core import AtlasEntity, AtlasProcess
from pyapacheatlas.readers.util import *

RELATIONSHIP_TYPE_DEFS = [
        {
      "category": "RELATIONSHIP",
      "name": "demo_table_columns",
      "endDef1": {
        "type": "demo_table",
        "name": "columns",
        "cardinality": "SET",
      },
      "endDef2": {
        "type": "demo_column",
        "name": "table",
        "cardinality": "SINGLE",
      },
      "relationshipCategory": "COMPOSITION"
    },
    # adding bad data
    {"category":"RELATIONSHIP"},
    {
      "category": "RELATIONSHIP",
      "name": "demo_process_column_lineage",
      "endDef1": {
        "type": "demo_column_lineage",
        "name": "query",
        "cardinality": "SINGLE",
      },
      "endDef2": {
        "type": "demo_process",
        "name": "columnLineages",
        "cardinality": "SET",
      },
      "relationshipCategory": "COMPOSITION"
    }
    ]


def test_first_entity_matching_attribute():
    atlas_entities = [
        AtlasEntity(
            name="demoentity",
            typeName="demo_table",
            qualified_name="demoentity",
            guid = -1000
        ),
        AtlasEntity(
            name="demoentity2",
            typeName="demo2_table",
            qualified_name="demoentity2",
            guid = -1001
        )
    ]
    results = first_entity_matching_attribute("name","demoentity", atlas_entities)

    assert (results.typeName == "demo_table")


def test_first_relationship_that_matches():

    results = first_relationship_that_matches("endDef1", "demo_column_lineage", "query", RELATIONSHIP_TYPE_DEFS)
    expected = {
      "category": "RELATIONSHIP",
      "name": "demo_process_column_lineage",
      "endDef1": {
        "type": "demo_column_lineage",
        "name": "query",
        "cardinality": "SINGLE",
      },
      "endDef2": {
        "type": "demo_process",
        "name": "columnLineages",
        "cardinality": "SET",
      },
      "relationshipCategory": "COMPOSITION"
    }
    assert(results == expected)


def test_first_process_matching_io():
    atlas_entities = [
        AtlasEntity(
            name="demoentity",
            typeName="demo_table",
            qualified_name="demoentity",
            guid = -1000
        ),
        AtlasEntity(
            name="demoentity2",
            typeName="demo2_table",
            qualified_name="demoentity2",
            guid = -1001
        )
    ]
    atlas_proc = AtlasProcess(
            name="demo_process_name",
            typeName="demo_process",
            qualified_name="demo_process_qualifier",
            inputs=[atlas_entities[0].to_json(minimum=True)],
            outputs=[atlas_entities[1].to_json(minimum=True)],
            guid = -1002
    )
    atlas_proc_no_in = AtlasProcess(
            name="demo_process_qualifier_no_in",
            typeName="demo_process1",
            qualified_name="demo_process_qualifier_no_in",
            inputs=[],
            outputs=[atlas_entities[1].to_json(minimum=True)],
            guid = -1003
    )
    atlas_proc_no_out = AtlasProcess(
            name="demo_process_qualifier_no_out",
            typeName="demo_process2",
            qualified_name="demo_process_qualifier_no_out",
            inputs=[atlas_entities[0].to_json(minimum=True)],
            outputs=[],
            guid = -1004
    )
    atlas_entities.extend([atlas_proc, atlas_proc_no_in, atlas_proc_no_out])
    

    results = first_process_matching_io(
        atlas_entities[0].attributes["qualifiedName"], 
        atlas_entities[1].attributes["qualifiedName"], 
        atlas_entities
    )

    assert(results.typeName == "demo_process")
    assert(results.attributes["qualifiedName"] == "demo_process_qualifier")


def test_from_process_lookup_col_lineage():
    entities = [
        AtlasProcess(
            name="demo_process_name",
            typeName="demo_process",
            qualified_name="demo_process_qualifier",
            inputs=[],
            outputs=[],
            guid = -1002,
            relationshipAttributes=[{"name":"dummy"}, {"name":"columnLineages", "typeName":"array<demo_column_lineage>"}]
        ),
        AtlasProcess(
                name="demo_process_qualifier_no_in",
                typeName="demo_process1",
                qualified_name="demo_process_qualifier_no_in",
                inputs=[],
                outputs=[],
                guid = -1003
        ),
        AtlasProcess(
                name="demo_process_qualifier_no_out",
                typeName="demo_process2",
                qualified_name="demo_process_qualifier_no_out",
                inputs=[],
                outputs=[],
                guid = -1004
        )
    ]
    process_col_lineage = from_process_lookup_col_lineage("demo_process_name", entities, RELATIONSHIP_TYPE_DEFS)

    assert(process_col_lineage == "demo_column_lineage")

    
def test_columns_matching_pattern():
    row = {"source attrib1":"test", "target attrib2":"results"}
    results = columns_matching_pattern(row, "source")
    assert(len(results) == 1)
    assert(set(results) == set(["attrib1"]))

def test_columns_matching_pattern_eliminate():
    row = {"source attrib1":"test", "source data_type":"test2", "source req":"test3","target attrib2":"results"}
    results = columns_matching_pattern(row, "source", does_not_match=["source req"])
    assert(len(results)==2)
    assert(set(results) == set(["attrib1", "data_type"]))

