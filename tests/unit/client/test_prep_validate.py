import json
from pyapacheatlas.core import AtlasClient, AtlasEntity
from pyapacheatlas.core.typedef import EntityTypeDef

sample_entity = {
      "typeName": "hive_column",
      "attributes": {
        "owner": "admin",
        "replicatedTo": [],
        "replicatedFrom": [],
        "qualifiedName": "hivedbtest.point_derived.y_value@primary",
        "name": "y_value",
        "description": None,
        "comment": None,
        "position": 1,
        "type": "int",
        "table": {
          "guid": "79e5659a-70c9-4ac9-bced-d28ac86a60cd",
          "typeName": "hive_table"
        }
      },
      "guid": "95f5da92-545b-44ac-8393-427f706cc7bb",
      "relationshipAttributes": {
        "inputToProcesses": [],
        "schema": [],
        "attachedSchema": [],
        "meanings": [],
        "table": {
          "guid": "79e5659a-70c9-4ac9-bced-d28ac86a60cd",
          "typeName": "hive_table",
          "entityStatus": "ACTIVE",
          "displayText": "point_derived",
          "relationshipType": "hive_table_columns",
          "relationshipGuid": "1dc9aed8-011e-4c0f-b879-90ba3c59ef78",
          "relationshipStatus": "ACTIVE",
          "relationshipAttributes": {
            "typeName": "hive_table_columns"
          }
        }
    }
}


def test_prepare_bulk_entity_from_list():
    results = AtlasClient._prepare_entity_upload([sample_entity])

    expected = {"entities": [sample_entity]}

    assert(results == expected)

def test_prepare_bulk_entity_from_dict():
    results = AtlasClient._prepare_entity_upload({"entities":[sample_entity]})

    expected = {"entities": [sample_entity]}

    assert(results == expected)

def test_prepare_bulk_entity_from_atlas_entity():

    class_entity = AtlasEntity(
        name=sample_entity["attributes"]["name"], 
        typeName=sample_entity["typeName"], 
        qualified_name=sample_entity["attributes"]["qualifiedName"],
        attributes=sample_entity["attributes"],
        guid=sample_entity["guid"],
        relationshipAttributes= sample_entity["relationshipAttributes"]
    )

    results = AtlasClient._prepare_entity_upload(class_entity)

    expected = {"entities": [sample_entity]}

    assert(results == expected)

def test_prepare_bulk_entity_from_mixed_atlas_entity_dict():

    class_entity = AtlasEntity(
        name=sample_entity["attributes"]["name"],
        typeName=sample_entity["typeName"],
        qualified_name=sample_entity["attributes"]["qualifiedName"],
        attributes=sample_entity["attributes"],
        guid=sample_entity["guid"],
        relationshipAttributes= sample_entity["relationshipAttributes"]
    )
    class_entity2 = AtlasEntity(
        name=sample_entity["attributes"]["name"]+"abc",
        typeName=sample_entity["typeName"],
        qualified_name=sample_entity["attributes"]["qualifiedName"]+"abc",
        attributes=sample_entity["attributes"],
        guid=sample_entity["guid"],
        relationshipAttributes= sample_entity["relationshipAttributes"]
    )

    results = AtlasClient._prepare_entity_upload(
        [class_entity, class_entity2.to_json()]
    )

    sample2 = sample_entity.copy()
    sample2["attributes"]["name"] = sample2["attributes"]["name"]+"abc"
    sample2["attributes"]["qualifiedName"] = sample2["attributes"]["qualifiedName"]+"abc"

    expected = {"entities": [
        sample_entity, sample2
    ]}

    assert(results == expected)

def test_prepare_type_def():
    e = EntityTypeDef("pyapacheatlas_test1")
    e2 = EntityTypeDef("pyapacheatlas_test2")
    e3 = EntityTypeDef("pyapacheatlas_test3")
    
    results = AtlasClient._prepare_type_upload(
        entityDefs = [e, e2.to_json(), e3],
    )
    assert(len(results["entityDefs"]) == 3)
    assert( all( [isinstance(r, dict) for r in results["entityDefs"]]))