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
        if sourceType == "sql server" and objectType == "table":
            return SqlServerTableMapper(asset, termMap)
        if sourceType == "sql server" and objectType == "database":
            return SqlServerDatabaseMapper(asset, termMap)
        else:
            raise ValueError(f"DataSource not supported: {dataSource}")