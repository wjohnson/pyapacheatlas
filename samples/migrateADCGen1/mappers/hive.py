from .assetmapper import AssetMapper

class HiveTableMapper(AssetMapper):
    def __init__(self, asset, termMap):
        super().__init__(asset, termMap, typeName='hive_table', columnTypeName='hive_column')
        data_source = asset["content"]["properties"]["dsl"]["address"]
        self.server = data_source["server"]
        self.database = data_source["database"]
        self.table = data_source["object"]

    def qualified_name(self):
        output = f"{self.database}.{self.table}@{self.server}"
        return output

    def column_qualified_name_pattern(self, columnName):
        output = f"{self.database}.{self.table}.{columnName}@{self.server}"
        return output

class HiveDatabaseMapper(AssetMapper):
    def __init__(self, asset, termMap):
        super().__init__(asset, termMap, typeName='hive_db', columnTypeName='column')
        data_source = asset["content"]["properties"]["dsl"]["address"]
        self.server = data_source["server"]
        self.database = data_source["database"]

    def qualified_name(self):
        output = f"{self.database}@{self.server}"
        return output

    def column_qualified_name_pattern(self, columnName):
        return "BADDATA"
    
    def entity(self, guid):
        local_entity = super().entity(guid)
        local_entity.attributes.update({"clusterName": self.server})
        return local_entity
