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

# if __name__ == "__main__":
#     oauth = ServicePrincipalAuthentication(
#         tenant_id=os.environ.get("TENANT_ID", "72f988bf-86f1-41af-91ab-2d7cd011db47"),
#         client_id=os.environ.get("CLIENT_ID", "0cd96de1-398d-4f4d-8dae-67a7b576a15f"),
#         client_secret=os.environ.get("CLIENT_SECRET", "")
#     )
#     client = PurviewClient(
#         account_name = os.environ.get("PURVIEW_NAME", "wjpurview001"),
#         authentication=oauth
#     )
#     dbResponse = client.get_entity(guid="65ec0fd8-1de0-4164-97ec-3b88cb000fdb") 
#     print(json.dumps(dbResponse, indent=2))

#     collResponse = client.get_entity(guid="bd53e412-0d08-442f-a8da-2286b97aac3a") 
#     print(json.dumps(collResponse, indent=2))