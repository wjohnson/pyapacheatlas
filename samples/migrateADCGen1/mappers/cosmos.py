from .assetmapper import AssetMapper

class CosmosDatabase(AssetMapper):

    def __init__(self, asset, termMap, typeName='azure_cosmosdb_database', columnTypeName='column'): #CHANGE TYPE NAME #guid=65ec0fd8-1de0-4164-97ec-3b88cb000fdb
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)

    def qualified_name(self):
        url = self.asset["properties"].get("dsl", {}).get("address", {}).get("url", None)
        db = self.asset["properties"].get("dsl", {}).get("address", {}).get("database", None)
        return f"{url}dbs/{db}"

    def column_qualified_name_pattern(self, columnName, **kwargs):
        return columnName

class CosmosDatabaseCollections(AssetMapper):

    def __init__(self, asset, termMap, typeName='azure_cosmosdb_sqlapi_collection', columnTypeName='column'): #guid=bd53e412-0d08-442f-a8da-2286b97aac3a
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)

    def qualified_name(self):
        url = self.asset["properties"].get("dsl", {}).get("address", {}).get("url", None)
        db = self.asset["properties"].get("dsl", {}).get("address", {}).get("database", None)
        coll = self.asset["properties"].get("dsl", {}).get("address", {}).get("collection", None)
        return f"{url}dbs/{db}/colls/{coll}"

    def column_qualified_name_pattern(self, columnName, **kwargs):
        return columnName
