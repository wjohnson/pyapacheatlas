import sys
sys.path.append("./")
from mappers.cosmos import CosmosDatabase
from mappers.cosmos import CosmosDatabaseCollections
import sys
sys.path.append("./")


CORE_TERMS = {"TERMID123": "term123@Glossary"}

CORE_ENTITY = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "url": "https://cosmos.documents.azure.com/",
                    "database": "Core"
                },
                "protocol": "document-db",
                "authentication": "azure-access-key"
            },
            "dataSource": {
                "sourceType": "Azure DocumentDB",
                "objectType": "Database"
            }
        }
    }
}

COLLECTION_ENTITY = {
    "content": {
        "properties": {
            "name": "Ticket",
            "dsl": {
                    "address": {
                        "url": "https://cosmos.documents.azure.com/",
                        "database": "Core",
                        "collection": "items"
                    },
            },
            "dataSource": {
                "sourceType": "Azure DocumentDB",
                "objectType": "Collection"
            }
        }
    }
}

db = CosmosDatabase(CORE_ENTITY, CORE_TERMS) 
coll = CosmosDatabaseCollections(COLLECTION_ENTITY, CORE_TERMS)


def test_cosmos_qualified_nameDB():
    assert(db.qualified_name() ==
           "https://cosmos.documents.azure.com/dbs/Core")


def test_cosmos_qualified_nameColls():
    assert(coll.qualified_name() ==
           "https://cosmos.documents.azure.com/dbs/Core/colls/items")


# def test_sql_table_has_schema_rel_attrib():  # check
#     e = sstm.entity(guid=-1)
#     exp_qualified_name = "mssql://my-server.database.windows.net/mydb/dbo"

#     assert("dbSchema" in e.relationshipAttributes)
#     dbSchema = e.relationshipAttributes["dbSchema"]
#     assert(dbSchema["typeName"] == "azure_sql_schema")
#     assert(dbSchema["uniqueAttributes"]["qualifiedName"] == exp_qualified_name)
