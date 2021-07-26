from .adlsg1 import ADLSGen1Directory, ADLSGen1DataLake
from .cosmos import CosmosDatabase, CosmosDatabaseCollections
from .hive import HiveTableMapper, HiveDatabaseMapper
from .oracle import OracleTableMapper, OracleViewMapper, OracleDatabaseMapper
from .sqlserver import SqlServerDatabaseMapper, SqlServerTableMapper

class AssetFactory():
    """
    Provides a means of creating 
    """
    @staticmethod
    def map_asset(asset, termMap):
        dataSource = asset.get("content", {}).get(
            "properties", {}).get("dataSource", {})
        sourceType = dataSource.get("sourceType", "").lower()
        objectType = dataSource.get("objectType", "").lower()
        if sourceType == "" or objectType == "":
            raise ValueError(f"DataSource not supported: {dataSource}")
        if sourceType == "azure data lake store" and objectType == "directory":
            return ADLSGen1Directory(asset, termMap)
        
        if sourceType == "azure documentdb" and objectType == "collection":
            return CosmosDatabaseCollections(asset, termMap)
        if sourceType == "azure documentdb" and objectType == "database":
            return CosmosDatabase(asset, termMap)
        
        if sourceType == "hive" and objectType == "table":
            return HiveTableMapper(asset, termMap)
        if sourceType == "hive" and objectType == "database":
            return HiveDatabaseMapper(asset, termMap)
        
        if sourceType == "oracle database" and objectType == "table":
            return OracleTableMapper(asset, termMap)
        if sourceType == "oracle database" and objectType == "database":
            return OracleDatabaseMapper(asset, termMap)
        if sourceType == "oracle database" and objectType == "view":
            return OracleViewMapper(asset, termMap)
        
        if sourceType == "sql server" and objectType == "table":
            return SqlServerTableMapper(asset, termMap)
        if sourceType == "sql server" and objectType == "database":
            return SqlServerDatabaseMapper(asset, termMap)
        else:
            raise ValueError(f"DataSource not supported: {dataSource}")