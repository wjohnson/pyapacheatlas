from .assetmapper import AssetMapper

class OracleMixIn(AssetMapper):
    def __init__(self, asset, termMap, typeName, columnTypeName):
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)
        data_source = asset["content"]["properties"]["dsl"]["address"]
        self.server = data_source.get("server", "")
        self.database = data_source.get("database", "")
        self.schema = data_source.get("schema", "")
        self.objectName = data_source.get("object", "")
    
    def _qualified_name_hierarchy(self, level, column=None):
        output = f"oracle://{self.server}"
        if level in ["database", "schema", "object", "column"]:
            output = output + "/" + self.database
        if level in ["schema", "object", "column"]:
            output = output + "/" + self.schema
        if level in ["object", "column"]:
            output = output + "/" + self.objectName
        if level in ["column"]:
            output = output + "/" + column

        return output


class OracleTableMapper(OracleMixIn):
    def __init__(self, asset, termMap):
        super().__init__(asset, termMap, typeName='oracle_table', columnTypeName='oracle_table_column')

    def qualified_name(self):
        output = self._qualified_name_hierarchy("object")
        return output

    def column_qualified_name_pattern(self, columnName):
        output = self._qualified_name_hierarchy("column", columnName)
        return output
    
    def entity(self, guid):
        local_entity = super().entity(guid)
        db_schema = {
            "typeName":"oracle_schema", 
            "uniqueAttributes":{"qualifiedName": self._qualified_name_hierarchy("database")}
        }
        local_entity.addRelationship(dbSchema = db_schema)
        return local_entity

class OracleViewMapper(OracleMixIn):
    def __init__(self, asset, termMap):
        super().__init__(asset, termMap, typeName='oracle_view', columnTypeName='oracle_view_column')
    
    def qualified_name(self):
        output = self._qualified_name_hierarchy("object")
        return output

    def column_qualified_name_pattern(self, columnName):
        output = self._qualified_name_hierarchy("column", columnName)
        return output
    
    def entity(self, guid):
        local_entity = super().entity(guid)
        db_schema = {
            "typeName":"oracle_schema", 
            "uniqueAttributes":{"qualifiedName": self._qualified_name_hierarchy("database")}
        }
        local_entity.addRelationship(dbSchema = db_schema)
        return local_entity

class OracleDatabaseMapper(OracleMixIn):
    def __init__(self, asset, termMap):
        super().__init__(asset, termMap, typeName='oracle_schema', columnTypeName='column')
    
    def qualified_name(self):
        output = self._qualified_name_hierarchy("server")
        return output

    def column_qualified_name_pattern(self, columnName):
        return "BADDATA"
    
    def entity(self, guid):
        local_entity = super().entity(guid)
        server = {
            "typeName":"oracle_server", 
            "uniqueAttributes":{"qualifiedName": self._qualified_name_hierarchy("server")}
        }
        local_entity.addRelationship(server = server)
        return local_entity