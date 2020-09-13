import warnings

import pytest

from pyapacheatlas.core.typedef import AtlasAttributeDef
from pyapacheatlas.readers.reader import Reader, ReaderConfiguration


def test_parse_bulk_entities():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "typeName", "name",
    # "qualifiedName", "classifications"
    json_rows = [
        {"typeName": "demoType", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC", "classifications": None
         },
        {"typeName": "demoType", "name": "entityNameGHI",
         "qualifiedName": "qualifiedNameofEntityNameGHI", "classifications": "PII;CLASS2"
         },
        {"typeName": "demoType", "name": "entityNameJKL",
         "qualifiedName": "qualifiedNameofEntityNameJKL", "classifications": "PII"
         },
        {"typeName": "demoType", "name": "entityNameDynamic",
         "qualifiedName": "qualifiedNameofEntityNameDynamic", "classifications": None,
         "dynamicAttrib1": "foo", "dynamicAttrib2": "bar"
         }
    ]
    results = reader.parse_bulk_entities(json_rows)

    assert("entities" in results)
    assert(len(results["entities"]) == len(json_rows))
    abc = results["entities"][0]
    ghi = results["entities"][1]
    jkl = results["entities"][2]
    dynamic = results["entities"][3]

    assert("classifications" not in abc)
    assert(len(ghi["classifications"]) == 2)
    assert(len(jkl["classifications"]) == 1)

    assert(jkl["classifications"][0]["typeName"] == "PII")
    ghi_classification_types = set(
        [x["typeName"] for x in ghi["classifications"]]
    )
    assert(set(["PII", "CLASS2"]) == ghi_classification_types)

    assert ("dynamicAttrib1" in dynamic["attributes"])
    assert (dynamic["attributes"]["dynamicAttrib1"] == "foo")
    assert ("dynamicAttrib2" in dynamic["attributes"])
    assert (dynamic["attributes"]["dynamicAttrib2"] == "bar")


def test_parse_bulk_entities_with_relationships():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "typeName", "name",
    # "qualifiedName", "classifications",
    # "(Relationship) table"
    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC", "classifications": None,
         "(Relationship) table": None
         },
        {"typeName": "demo_column", "name": "col1",
         "qualifiedName": "col1qn", "classifications": None,
         "(Relationship) table": "qualifiedNameofEntityNameABC"
         },
         {"typeName": "demo_column", "name": "col2",
         "qualifiedName": "col2qn", "classifications": None,
         "(Relationship) table": None
         }
    ]
    results = reader.parse_bulk_entities(json_rows)
    abc = results["entities"][0]
    col1 = results["entities"][1]
    col2 = results["entities"][2]

    assert("table" in col1["relationshipAttributes"])
    col1_table = col1["relationshipAttributes"]["table"]
    assert(col1_table["typeName"] == "demo_table" )
    assert(col1_table["qualifiedName"] == "qualifiedNameofEntityNameABC" )

    assert("table" not in col2["relationshipAttributes"])


def test_parse_entity_defs():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "Entity TypeName", "name", "description",
    # "isOptional", "isUnique", "defaultValue",
    # "typeName", "displayName", "valuesMinCount",
    # "valuesMaxCount", "cardinality", "includeInNotification",
    # "indexType", "isIndexable"
    json_rows = [
        {
            "Entity TypeName": "demoType",
            "name": "attrib1",
            "description": "Some desc",
            "isOptional": "True",
            "isUnique": "False",
            "defaultValue": None,
            "typeName": "string",
            "displayName": None,
            "valuesMinCount": None,
            "valuesMaxCount": None,
            "cardinality": None,
            "includeInNotification": None,
            "indexType": None,
            "isIndexable": None
        }
    ]

    results = reader.parse_entity_defs(json_rows)

    assert("entityDefs" in results)
    assert(len(results["entityDefs"]) == 1)
    assert(results["entityDefs"][0]["attributeDefs"][0]["name"] == "attrib1")


def test_parse_entity_defs_extended():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    json_rows = [
        {"Entity TypeName": "generic", "name": "attrib1", "description": "desc1",
         "isOptional": "True", "isUnique": "False", "defaultValue": None},
        {"Entity TypeName": "generic", "name": "attrib2", "description": "desc2",
         "isOptional": "True", "isUnique": "False", "defaultValue": None,
         "cardinality": "SINGLE"},
        {"Entity TypeName": "demo", "name": "attrib3", "description": "desc3",
         "isOptional": "False", "isUnique": "False", "cardinality": "SET"}
    ]

    output = reader.parse_entity_defs(json_rows)
    # It is an AtlasTypesDef composite wrapper
    assert("entityDefs" in output.keys())
    # There are two entity typenames specified so there should be only two entityDefs
    assert (len(output["entityDefs"]) == 2)

    genericEntityDef = None
    demoEntityDef = None

    for entityDef in output["entityDefs"]:
        if entityDef["name"] == "generic":
            genericEntityDef = entityDef
        elif entityDef["name"] == "demo":
            demoEntityDef = entityDef

    # Generic has two attributes
    assert(len(genericEntityDef["attributeDefs"]) == 2)

    # Demo has one attribute
    assert(len(demoEntityDef["attributeDefs"]) == 1)

    assert(
        demoEntityDef["attributeDefs"][0] == AtlasAttributeDef(
            name="attrib3", **{"description": "desc3", "isOptional": "False",
                               "isUnique": "False", "cardinality": "SET"}
        ).to_json()
    )


def test_entityDefs_warns_with_extra_params():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # All attribute keys should be converted to camel case except "Entity TypeName"
    inputData = [
        {"Entity TypeName": "generic", "name": "attrib1", "description": "desc1",
         "isOptional": "True", "isUnique": "False", "defaultValue": None},
        {"Entity TypeName": "generic", "name": "attrib2", "description": "desc2",
         "isOptional": "True", "isUnique": "False", "defaultValue": None,
         "cardinality": "SINGLE", "randomAttrib": "foobar"}
    ]

    # Assert that a UserWarning occurs when adding an extra attribute
    pytest.warns(UserWarning, reader.parse_entity_defs,
                 **{"json_rows": inputData})
