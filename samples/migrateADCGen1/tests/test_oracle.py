import sys
sys.path.append("./")

from mappers.oracle import OracleViewMapper
from mappers.oracle import OracleTableMapper
from mappers.oracle import OracleDatabaseMapper

CORE_TERMS = {"TERMID123": "term123@Glossary"}

DB = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "server": "server.name:port/schemaName",
                    "database": "dbName"
                },
                "protocol": "oracle",
                "authentication": "protocol"
            },
            "dataSource": {
                "sourceType": "Oracle Database",
                "objectType": "Database"
            }
        }
    }
}

TABLE = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "server": "server.name:port",
                    "database": "dbName",
                    "schema": "schemaName",
                    "object": "tableName"
                },
                "protocol": "oracle",
                "authentication": "protocol"
            },
            "dataSource": {
                "sourceType": "Oracle Database",
                "objectType": "Table"
            }
        }
    }
}


VIEW = {
    "content": {
        "properties": {
            "dsl": {
                "address": {
                    "server": "server.name:port",
                    "database": "dbName",
                    "schema": "schemaName",
                    "object": "viewName"
                },
            },
            "dataSource": {
                "sourceType": "Oracle Database",
                "objectType": "View"
            },
        }
    }
}

odb = OracleDatabaseMapper(DB, CORE_TERMS)
otbl = OracleTableMapper(TABLE, CORE_TERMS)
ovw = OracleViewMapper(VIEW, CORE_TERMS)


def test_oracle_db_qualified_name():
    assert(odb.qualified_name() ==
           "oracle://server.name:port/schemaName")


def test_oracle_db_has_required_rel_attributes():
    e = odb.entity(-1)
    assert("server" in e.relationshipAttributes)
    assert(e.relationshipAttributes["server"]["uniqueAttributes"].get(
        "qualifiedName") == "oracle://server.name:port")


def test_oracle_view_qualified_name():
    assert(ovw.qualified_name() ==
           "oracle://server.name:port/dbName/schemaName/viewName")


def test_oracle_view_column_qualified_name():
    # oracle_view_column
    assert(ovw.column_qualified_name_pattern("columnName") ==
           "oracle://server.name:port/dbName/schemaName/viewName/columnName")


def test_oracle_view_has_required_rel_attributes():
    e = ovw.entity(-1)
    assert("dbSchema" in e.relationshipAttributes)
    assert(e.relationshipAttributes["dbSchema"]["uniqueAttributes"].get(
        "qualifiedName") == "oracle://server.name:port/dbName/schemaName")


def test_oracle_table_qualified_name():
    assert(otbl.qualified_name() ==
           "oracle://server.name:port/dbName/schemaName/tableName")


def test_oracle_table_column_qualified_name():
    # oracle_view_column
    assert(otbl.column_qualified_name_pattern("columnName") ==
           "oracle://server.name:port/dbName/schemaName/tableName/columnName")


def test_oracle_table_has_required_rel_attributes():
    e = otbl.entity(-1)
    assert("dbSchema" in e.relationshipAttributes)
    assert(e.relationshipAttributes["dbSchema"]["uniqueAttributes"].get(
        "qualifiedName") == "oracle://server.name:port/dbName/schemaName")
