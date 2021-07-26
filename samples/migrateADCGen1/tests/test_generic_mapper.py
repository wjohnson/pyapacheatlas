import sys
sys.path.append("./")

# Need some implementation of the asset mapper
from mappers.sqlserver import SqlServerTableMapper


CORE_TERMS = {"TERMID123": "term123@Glossary",
              "TERMID456": "termid456@Glossary"}

CORE_ENTITY = {
    "content": {
        "id": "SQLTABLETEST",
        "properties": {
            "name": "Assessment",
            "dsl": {
                "address": {
                    "server": "server",
                    "database": "db",
                    "schema": "dbo",
                    "object": "tbl"
                },
            },
            "dataSource": {
                "sourceType": "SQL Server",
                "objectType": "Table"
            }
        },
        "annotations": {
            "columnDescriptions": [
                {
                    "properties": {
                        "columnName": "Id",
                        "description": "This is the primary key"
                    },
                }
            ],
            "termTags": [
                {
                    "properties": {
                        "termId": "TERMID123",
                    }
                }
            ],
            "columnTermTags": [
                {
                    "properties": {
                        "columnName": "Id",
                        "termId": "TERMID456",
                    },
                }
            ],
            "experts": [
                {
                    "properties": {
                        "expert": {
                            "objectId": "abc-123-def",
                            "upn": "test@example"
                        }
                    }

                }
            ],
            "schema": {
                "properties": {
                    "columns": [
                      {
                          "name": "Id",
                          "type": "uniqueidentifier",
                          "maxLength": 16,
                          "precision": 0,
                          "isNullable": False
                      }
                    ],
                }
            },
            "tags": [
                {
                    "id": "TAG123",
                    "properties": {
                        "tag": "testing"
                    },
                }
            ],
            "friendlyName": {
                "properties": {
                    "friendlyName": "Assessment DB",
                }
            },
            "descriptions": [
                {
                    "properties": {
                        "description": "This is my description of the db"
                    }
                }
            ]
        }
    }
}

MAPPER = SqlServerTableMapper(CORE_ENTITY, CORE_TERMS)


# Generic tests
def test_partial_column_updates_column_descs():

    results = MAPPER.partial_column_updates()
    first_entry = results[0]

    assert(first_entry["attributes"] == {
           "description": "This is the primary key"})


def test_partial_entity_updates_friendlyName_description():
    results = MAPPER.partial_entity_updates()

    attribs = results["attributes"]

    assert(attribs == {
        "name": "Assessment DB",
        "description": "This is my description of the db"})


def test_glossary_entity_relationships():
    results = MAPPER.glossary_entity_relationships()
    first_entry = results[0]

    assert(first_entry["end1"]["uniqueAttributes"]
           ["qualifiedName"] == "term123@Glossary")
    assert(all([k in ["typeName", "uniqueAttributes"]
                for k in first_entry["end2"].keys()]))


def test_glossary_column_relationships():
    results = MAPPER.glossary_column_relationships()
    first_entry = results[0]

    assert(first_entry["end1"]["uniqueAttributes"]
           ["qualifiedName"] == "termid456@Glossary")
    assert(all([k in ["typeName", "uniqueAttributes"]
                for k in first_entry["end2"].keys()]))


def test_entity_has_experts():
    e = MAPPER.entity(guid=-1)

    assert(hasattr(e, "contacts"))
    e.contacts == {"Expert":[{"id":"abc-123-def"}], "Owner":[]}
