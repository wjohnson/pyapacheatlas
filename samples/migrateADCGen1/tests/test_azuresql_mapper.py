import sys
sys.path.append("./")

from mappers.sqlserver import SqlServerTableMapper
from mappers.sqlserver import SqlServerDatabaseMapper


CORE_TERMS = {"TERMID123": "term123@Glossary"}

CORE_ENTITY = {
    "content": {
        "id": "SQLTABLETEST",
        "properties": {
            "name": "Assessment",
            "dsl": {
                "address": {
                    "server": "my-server.database.windows.net",
                    "database": "mydb",
                    "schema": "dbo",
                    "object": "mytable"
                },
            },
            "dataSource": {
                "sourceType": "SQL Server",
                "objectType": "Table"
            }
        }
    }
}

sstm = SqlServerTableMapper(CORE_ENTITY, CORE_TERMS)
def test_sql_table_qualified_name():
    assert(sstm.qualified_name() ==
           "mssql://my-server.database.windows.net/mydb/dbo/mytable")


def test_sql_column_qualified_name_pattern():
    assert(sstm.column_qualified_name_pattern("testcol") ==
           "mssql://my-server.database.windows.net/mydb/dbo/mytable#testcol")

def test_sql_table_has_schema_rel_attrib():
    e = sstm.entity(guid=-1)
    exp_qualified_name = "mssql://my-server.database.windows.net/mydb/dbo"

    assert("dbSchema" in e.relationshipAttributes)
    dbSchema = e.relationshipAttributes["dbSchema"]
    assert(dbSchema["typeName"] == "azure_sql_schema")
    assert(dbSchema["uniqueAttributes"]["qualifiedName"] == exp_qualified_name)
    
