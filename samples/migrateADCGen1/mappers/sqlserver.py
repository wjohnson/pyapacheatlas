from .assetmapper import AssetMapper

class SqlServerTableMapper(AssetMapper):

    def __init__(self, asset, terms, typeName="azure_sql_table", columnTypeName="azure_sql_column"):
        super().__init__(asset, terms, typeName, columnTypeName)
        _address = self.asset["properties"]["dsl"]["address"]
        self.server = _address["server"]
        self.database = _address["database"]
        self.schema = _address["schema"]
        self.table = _address["object"]
        self.friendlyName = _address["object"]

    def entity(self, guid):
        local_entity = super().entity(guid)
        # Need to add the required relationship attributes
        db_schema = {
            "typeName":"azure_sql_schema", 
            "uniqueAttributes":{"qualifiedName": self.qualified_name("schema")}
        }
        local_entity.addRelationship(dbSchema = db_schema)
        return local_entity

    def qualified_name(self, level="table"):
        output = f"mssql://{self.server}"
        if level in ["database", "schema", "table"]:
            output = output + "/" + self.database
        if level in ["schema", "table"]:
            output = output + "/" + self.schema
        if level in ["table"]:
            output = output + "/" + self.table

        return output

    def column_qualified_name_pattern(self, columnName):
        return self.qualified_name() + "#" + columnName

class SqlServerDatabaseMapper(AssetMapper):

    def __init__(self, asset, terms, typeName="azure_sql_db", columnTypeName="azure_sql_column"):
        super().__init__(asset, terms, typeName, columnTypeName)
        _address = self.asset["properties"]["dsl"]["address"]
        self.server = _address["server"]
        self.database = _address["database"]
        self.friendlyName = _address["database"]

    def entity(self, guid):
        local_entity = super().entity(guid)
        # Need to add the required relationship attributes
        server = {
            "typeName":"azure_sql_server", 
            "uniqueAttributes":{"qualifiedName": self.qualified_name("server")}
        }
        local_entity.addRelationship(server = server)
        return local_entity

    def qualified_name(self, level="database"):
        output = f"mssql://{self.server}"
        if level in ["database"]:
            output = output + "/" + self.database

        return output

    def column_qualified_name_pattern(self, columnName):
        return "BADDATA"
