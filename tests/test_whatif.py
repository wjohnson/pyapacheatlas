
from pyapacheatlas.scaffolding import column_lineage_scaffold
from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.whatif import WhatIfValidator

whatif = WhatIfValidator(column_lineage_scaffold("demo"))

def test_type_doesnt_exist():
    entities = [
        AtlasEntity("dummy1", "demo_table", "dummy1", -99).to_json(),
        AtlasEntity("dummy2", "foobar", "dummy1", -100).to_json()
    ]

    results = [whatif.entity_type_exists(e) for e in entities]

    assert(results[0] == True)
    assert(results[1] == False)

def test_missing_req_attributes():
    entities = [
        AtlasEntity("dummy1", "demo_table", "dummy1", -99, attributes = {"req_attrib":"1"}).to_json(),
        AtlasEntity("dummy2", "demo_table", "dummy1", -100).to_json()
    ]

    demo_table_type = {"entityDefs":[{'category': 'ENTITY', 'name': 'demo_table', 'attributeDefs': [{"name":"req_attrib","isOptional":False}], 'relationshipAttributeDefs': [], 'superTypes': ['DataSet']}]}

    local_what_if = WhatIfValidator(demo_table_type)

    results = [local_what_if.entity_missing_attributes(e) for e in entities]

    assert(results[0] == False)
    assert(results[1] == True)

def test_using_invalid_attributes():
    entities = [
        AtlasEntity("dummy1", "demo_table", "dummy1", -99, attributes = {"req_attrib":"1"}).to_json(),
        AtlasEntity("dummy2", "demo_table", "dummy1", -100, attributes = {"foo":"bar"}).to_json()
    ]

    demo_table_type = {"entityDefs":[{'category': 'ENTITY', 'name': 'demo_table', 
    'attributeDefs': [
        {"name":"req_attrib","isOptional":False},
        {"name":"name","isOptional":False},
        {"qualifiedName":"name","isOptional":False},
    ], 
    'relationshipAttributeDefs': [], 'superTypes': ['DataSet']}]}

    local_what_if = WhatIfValidator(demo_table_type)

    results = [local_what_if.entity_has_invalid_attributes(e) for e in entities]

    assert(results[0] == False)
    assert(results[1] == True)

def test_would_it_overwrite():
    entities = [
        AtlasEntity("dummy1", "demo_table", "dummy1", -99, attributes = {"req_attrib":"1"}).to_json(),
        AtlasEntity("dummy2", "demo_table", "dummy1", -100, attributes = {"foo":"bar"}).to_json()
    ]

    new_entity = AtlasEntity("dummy1", "demo_table", "dummy1", -99, attributes = {"req_attrib":"1"}).to_json()

    demo_table_type = {"entityDefs":[]}
    
    local_what_if = WhatIfValidator(existing_entities=entities)

    results = local_what_if.entity_would_overwrite(new_entity)

    assert(results)
