from .assetmapper import AssetMapper

class ADLSGen1Path(AssetMapper):

    def __init__(self, asset, termMap, typeName='azure_datalake_gen1_path', columnTypeName='column'):
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)

    def qualified_name(self):
        url = self.asset["properties"].get("dsl", {}).get("address", {}).get("url", None)
        return url

    def column_qualified_name_pattern(self, columnName, **kwargs):
        return columnName
    