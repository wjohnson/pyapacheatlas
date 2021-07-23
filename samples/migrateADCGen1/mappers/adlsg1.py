import sys
sys.path.append("./")
from .assetmapper import AssetMapper
from urllib.parse import urlparse

class ADLSGen1Directory(AssetMapper):

    def __init__(self, asset, termMap, typeName='azure_datalake_gen1_path', columnTypeName='column'):
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)

    def qualified_name(self):
        url = self.asset["properties"].get("dsl", {}).get("address", {}).get("url", None)
        parsed = urlparse(url)
        url = parsed.geturl().replace("https", "adl", 1)
        return f"{url}"

    def column_qualified_name_pattern(self, columnName, **kwargs):
        return columnName
    
    # Override
    def partial_column_updates(self):
        return []
    
class ADLSGen1DataLake(AssetMapper):

    def __init__(self, asset, termMap, typeName='azure_datalake_gen1_path', columnTypeName='column'):
        super().__init__(asset, termMap, typeName=typeName, columnTypeName=columnTypeName)

    def qualified_name(self):
        url = self.asset["properties"].get("dsl", {}).get("address", {}).get("url", None)
        parsed = urlparse(url)
        url = parsed.geturl().replace("https", "adl", 1)
        if url[-1] == "/":
            url = url[:-1]
        
        return f"{url}"

    def column_qualified_name_pattern(self, columnName, **kwargs):
        return columnName
    
    # Override
    def partial_column_updates(self):
        return []
