import json
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
         "qualifiedName": "qualifiedNameofEntityNameABC", "[root] classifications": None
         },
        {"typeName": "demoType", "name": "entityNameGHI",
         "qualifiedName": "qualifiedNameofEntityNameGHI", "[root] classifications": "PII;CLASS2"
         },
        {"typeName": "demoType", "name": "entityNameJKL",
         "qualifiedName": "qualifiedNameofEntityNameJKL", "[root] classifications": "PII"
         },
        {"typeName": "demoType", "name": "entityNameDynamic",
         "qualifiedName": "qualifiedNameofEntityNameDynamic", "[root] classifications": None,
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

    # The classifications should default to NOT propagate
    assert( all( [c["propagate"]==False for c in ghi["classifications"] + jkl["classifications"]] ))

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
    # "[Relationship] table"
    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "[Relationship] table": None
         },
        {"typeName": "demo_column", "name": "col1",
         "qualifiedName": "col1qn",
         "[Relationship] table": "qualifiedNameofEntityNameABC"
         },
         {"typeName": "demo_column", "name": "col2",
         "qualifiedName": "col2qn",
         "[Relationship] table": None
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

def test_parse_bulk_entities_with_relationships_and_atlas_object_id():
    rc = ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "[Relationship] table": None,
         "[Relationship] columns": "AtlasObjectId(guid:abc-123-def);AtlasObjectId(typeName:DataSet qualifiedName:qnInList)"
         },
        {"typeName": "demo_column", "name": "col1",
         "qualifiedName": "col1qn",
         "[Relationship] table": "AtlasObjectId(typeName:DataSet qualifiedName:myqualifiedName)",
         "[Relationship] columns": None
         },
         {"typeName": "demo_column", "name": "col2",
         "qualifiedName": "col2qn",
         "[Relationship] table": "AtlasObjectId(guid:ghi-456-jkl)",
         "[Relationship] columns": None
         }
    ]
    results = reader.parse_bulk_entities(json_rows)
    table = results["entities"][0]
    col1 = results["entities"][1]
    col2 = results["entities"][2]

    assert(len(table["relationshipAttributes"]["columns"]) == 2)
    assert(table["relationshipAttributes"]["columns"][0] == {"guid":"abc-123-def"})
    assert(table["relationshipAttributes"]["columns"][1] == {"typeName":"DataSet", "uniqueAttributes": {"qualifiedName":"qnInList"}})

    col1_table = col1["relationshipAttributes"]["table"]
    assert(col1_table["typeName"] == "DataSet" )
    assert(col1_table["uniqueAttributes"] == {"qualifiedName": "myqualifiedName"} )

    assert(col2["relationshipAttributes"]["table"] == {"guid":"ghi-456-jkl"})

def test_parse_bulk_entities_with_terms():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "typeName", "name",
    # "qualifiedName", "classifications",
    # "[Relationship] table"
    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "[Relationship] meanings": "My Term;abc"
         },
         {"typeName": "demo_table", "name": "entityNameDEF",
         "qualifiedName": "qualifiedNameofEntityNameDEF",
         "[Relationship] meanings": None
         }
    ]
    results = reader.parse_bulk_entities(json_rows)
    ae1 = results["entities"][0]
    ae2 = results["entities"][1]

    assert("meanings" in ae1["relationshipAttributes"])
    assert("meanings" not in ae2["relationshipAttributes"])
    ae1_meanings = ae1["relationshipAttributes"]["meanings"]

    assert(len(ae1_meanings) == 2)
    ae1_meanings_qns = set([e["uniqueAttributes"]["qualifiedName"] for e in ae1_meanings ])
    assert(set(["My Term@Glossary", "abc@Glossary"]) == ae1_meanings_qns)

def test_parse_bulk_entities_with_root_labels():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "typeName", "name",
    # "qualifiedName", "classifications",
    # "[Relationship] table"
    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC", "[root] classifications": None,
         "[root] labels": "labelA"
         },
         {"typeName": "demo_table", "name": "entityNameDEF",
         "qualifiedName": "qualifiedNameofEntityNameDEF", "[root] classifications": None,
         "[root] labels": "labelA;labelB", "[root] status": "ACTIVE"
         }
    ]
    results = reader.parse_bulk_entities(json_rows)
    ae1 = results["entities"][0]
    ae2 = results["entities"][1]
    
    assert("labels" in ae1 and "labels" in ae2)
    assert(ae1["labels"] == ["labelA"])
    assert(ae2["labels"] == ["labelA", "labelB"])
    
    assert(("status" not in ae1) and "status" in ae2)
    assert(ae2["status"] == "ACTIVE")

# TODO: classifications
# TODO: busines attributes
# TODO: custom attributes

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

def test_bulk_entity_with_experts_owners():
    rc =ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"typeName": "demoType", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "experts": "a;b;"
         },
        {"typeName": "demoType", "name": "entityNameGHI",
         "qualifiedName": "qualifiedNameofEntityNameGHI",
         "experts": "a;b;", "owners":"c;d"
         },
        {"typeName": "demoType", "name": "entityNameJKL",
         "qualifiedName": "qualifiedNameofEntityNameJKL",
         },
         {"typeName": "demoType", "name": "entityNameMNO",
         "qualifiedName": "qualifiedNameofEntityNameMNO",
         "owners": "e;f;"
         }
    ]

    results = reader.parse_bulk_entities(json_rows)

    assert("contacts" in results["entities"][0])
    exp_only = results["entities"][0]["contacts"]
    both = results["entities"][1]["contacts"]
    no_contacts = results["entities"][2]
    owner_only = results["entities"][3]["contacts"]

    assert(len(exp_only["Owner"]) == 0)
    assert(exp_only["Expert"] == [{"id":"a"}, {"id": "b"}])
    assert(both["Owner"] == [{"id":"c"}, {"id": "d"}])
    assert(both["Expert"] == [{"id":"a"}, {"id": "b"}])
    assert("contacts" not in no_contacts)
    assert(len(owner_only["Expert"]) == 0)
    assert(owner_only["Owner"] == [{"id":"e"}, {"id": "f"}])

def test_bulk_entity_with_experts_owners_func():
    rc =ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"typeName": "demoType", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "experts": "a;b;", "owners":""
         },
        {"typeName": "demoType", "name": "entityNameGHI",
         "qualifiedName": "qualifiedNameofEntityNameGHI",
         "experts": "a;b;", "owners":"c;d"
         },
        {"typeName": "demoType", "name": "entityNameJKL",
         "qualifiedName": "qualifiedNameofEntityNameJKL",
         }
    ]

    dummy_func = (lambda x: x+"_abc")

    results = reader.parse_bulk_entities(json_rows, contacts_func=dummy_func)

    exp_only = results["entities"][0]["contacts"]
    both = results["entities"][1]["contacts"]
    no_contacts = results["entities"][2]

    assert(len(exp_only["Owner"]) == 0)
    assert(exp_only["Expert"] == [{"id":"a_abc"}, {"id": "b_abc"}])
    assert(both["Owner"] == [{"id":"c_abc"}, {"id": "d_abc"}])
    assert(both["Expert"] == [{"id":"a_abc"}, {"id": "b_abc"}])
    assert("contacts" not in no_contacts)
    
def test_parse_classification_defs():
    rc =ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"classificationName": "testClassification", "entityTypes": None, "description": "This is my classification"},
        {"classificationName": "testClassification2", "entityTypes": "", "description": "This is my classification2"},
        {"classificationName": "testClassification3", "entityTypes": "DataSet;Process", "description": "This is my classification3"},
        {"classificationName": "testClassification4", "entityTypes": "DataSet;", "description": "This is my classification4"}
    ]

    parsed = reader.parse_classification_defs(json_rows)

    results = parsed["classificationDefs"]


    assert(len(results) == 4)
    assert("description" in results[0])
    assert(results[0]["name"] == "testClassification")
    assert(len(results[0]["entityTypes"]) == 0)
    assert(len(results[1]["entityTypes"]) == 0)
    assert(len(results[2]["entityTypes"]) == 2)
    assert(len(results[3]["entityTypes"]) == 1)

def test_parse_classification_defs_with_super_sub_types():
    rc =ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"classificationName": "test", "entityTypes": "DataSet", "superTypes": "a;b", "subTypes":"c;d"},
    ]

    parsed = reader.parse_classification_defs(json_rows)

    results = parsed["classificationDefs"]

    assert(results[0]["superTypes"] == ["a","b"])
    assert(results[0]["subTypes"] == ["c","d"])

def test_parse_column_mapping():
    rc = ReaderConfiguration()
    reader = Reader(rc)

    json_rows = [
        {"Source qualifiedName": "abc://123", "Source column":"A1", "Target qualifiedName": "def://456", "Target column": "B1", "Process qualifiedName": "proc://abc", "Process typeName": "customProcWithMapping", "Process name":"my proc name"},
        {"Source qualifiedName": "abc://123", "Source column":"A2", "Target qualifiedName": "def://456", "Target column": "B2", "Process qualifiedName": "proc://abc", "Process typeName": "customProcWithMapping", "Process name":"my proc name"},
        {"Source qualifiedName": "pqr://777", "Source column":"C1", "Target qualifiedName": "def://999", "Target column": "B3", "Process qualifiedName": "proc://abc", "Process typeName": "customProcWithMapping", "Process name":"my proc name"}
    ]

    parsed = reader.parse_column_mapping(json_rows)

    results = parsed

    assert(len(results) == 1)
    assert(results[0]["attributes"]["name"] == "my proc name")
    assert(results[0]["attributes"]["qualifiedName"] == "proc://abc")
    columnMapping = json.loads(results[0]["attributes"]["columnMapping"])
    assert(len(columnMapping) == 2)
    firstMap = columnMapping[0]
    firstMap_col_map = firstMap["ColumnMapping"]
    firstMap_data_map = firstMap["DatasetMapping"]
    firstMap_col_map_exp = [{"Source": "A1", "Sink": "B1"},{"Source": "A2", "Sink": "B2"}]
    firstMap_data_map_exp = {"Source": "abc://123", "Sink": "def://456"}
    assert(len(firstMap_col_map) == len(firstMap_col_map_exp))
    assert(len([i for i in firstMap_col_map if i in firstMap_col_map_exp]))
    assert(firstMap_data_map == firstMap_data_map_exp)
    
    secondMap = columnMapping[1]
    secondMap_col_map = secondMap["ColumnMapping"]
    secondMap_data_map = secondMap["DatasetMapping"]
    secondMap_col_map_exp = [{"Source": "C1", "Sink": "B3"}]
    secondMap_data_map_exp = {"Source": "pqr://777", "Sink": "def://999"}
    assert(secondMap_col_map == secondMap_col_map_exp)
    assert(secondMap_data_map == secondMap_data_map_exp)

def test_parse_bulk_entities_with_custom_attributes():
    rc = ReaderConfiguration()
    reader = Reader(rc)
    # "typeName", "name",
    # "qualifiedName",
    # "[custom] foo", "bar"
    json_rows = [
        {"typeName": "demo_table", "name": "entityNameABC",
         "qualifiedName": "qualifiedNameofEntityNameABC",
         "[custom] foo": "bar"
         },
         {"typeName": "demo_table", "name": "entityNameDEF",
         "qualifiedName": "qualifiedNameofEntityNameDEF",
         "[custom] foo": None
         }
    ]
    results = reader.parse_bulk_entities(json_rows)
    ae1 = results["entities"][0]
    ae2 = results["entities"][1]

    assert("foo" in ae1["customAttributes"])
    assert(ae1["customAttributes"]["foo"] == "bar")

    assert("customAttributes" not in ae2)
