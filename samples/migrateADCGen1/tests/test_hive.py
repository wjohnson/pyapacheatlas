import sys
sys.path.append("./")

from mappers.hive import HiveDatabaseMapper
from mappers.hive import HiveTableMapper

CORE_TERMS = {"TERMID123": "term123@Glossary"}

TABLE_ENTITY = {
    "content": {
        "properties": {
            "dsl": {
                "connectionProperties": {
                    "serverProtocol": "hive2"
                },
                "address": {
                    "server": "MyServer",
                    "database": "db",
                    "object": "tbl"
                },
            },
            "dataSource": {
                "sourceType": "Hive",
                "objectType": "Table"
            }
        }
    }
}

DB_ENTITY = {
    "content": {
        "properties": {
            "name": "default",
            "dsl": {
                    "connectionProperties": {"serverProtocol": "hive2"},
                    "address": {
                        "server": "MyServer",
                        "database": "db"
                    },
                "protocol": "hive",
                "authentication": "hdinsight"
            },
            "dataSource": {
                "sourceType": "Hive",
                "objectType": "Database"
            }
        }
    }
}

hive_table = HiveTableMapper(TABLE_ENTITY, CORE_TERMS)
hive_db = HiveDatabaseMapper(DB_ENTITY, CORE_TERMS)


def test_hive_table_qualified_name():
    assert(hive_table.qualified_name() ==
           "db.tbl@MyServer")


def test_hive_column_qualified_name():
    assert(hive_table.column_qualified_name_pattern("testcol") ==
           "db.tbl.testcol@MyServer")


def test_hive_db_qualified_name():
    assert(hive_db.qualified_name() ==
           "db@MyServer")

def test_hive_db_has_clusterName_attrib():
    e = hive_db.entity(-1)
    assert(e.attributes.get("clusterName", None) == "MyServer")