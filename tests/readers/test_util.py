from pyapacheatlas.core import AtlasEntity, AtlasProcess
from pyapacheatlas.readers.util import *

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


def test_child_type_from_relationship():
    
    type_defs = [
        {"name":"demo_table","relationshipAttributeDefs":[{"name":"columns","typeName":"array<demo_column>"}]},
        {"name":"demo2_table","relationshipAttributeDefs":[{"name":"xcolumns","typeName":"array<demo2_column>"}]}

    ]
    entity_type = "demo_table",
    relationship_name = "columns"

    results = child_type_from_relationship(entity_type, relationship_name, type_defs, normalize=True)

    assert(results == "demo_column")


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
    type_defs = [
        {"name":"demo_process","relationshipAttributeDefs":[{"name":"columnLineages","typeName":"array<demo_column_lineage>"}]},
        {"name":"demo2_table","relationshipAttributeDefs":[{"name":"xcolumns","typeName":"array<demo2_column>"}]}
    ]
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
    mapping, process_col_lineage = from_process_lookup_col_lineage("demo_process_name", {}, entities, type_defs)

    assert(process_col_lineage == "demo_column_lineage")