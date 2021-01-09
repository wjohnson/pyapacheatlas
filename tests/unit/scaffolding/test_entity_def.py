import json
from pyapacheatlas.scaffolding.entity_def import to_entity_def

def test_entity_def():

    attribute_names = ["x","y","z"]

    results = to_entity_def("generic", attribute_names)

    assert(len(results.get("attributeDefs")) == len(attribute_names))
    assert(results.get("name") == "generic")

    # make sure the follow the defaults
    for attrib in results.get("attributeDefs"):
        assert(attrib.get("name") in attribute_names)
        assert(attrib.get("typeName") == "string")
        assert(attrib.get("cardinality") == "SINGLE")



