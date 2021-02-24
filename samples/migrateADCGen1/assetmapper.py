from abc import ABC, abstractproperty
import json

from pyapacheatlas.core import AtlasEntity

class AssetFactory():
    @staticmethod
    def map_asset(asset):
        dataSource = asset.get("content", {}).get("properties",{}).get("dataSource", {})
        sourceType = dataSource.get("sourceType", "").lower()
        objectType = dataSource.get("objectType", "").lower()
        if sourceType == "" or objectType == "":
            raise ValueError(f"DataSource not supported: {dataSource}")
        if sourceType == "sql server" and objectType == "table":
            return SqlServerTableMapper(asset)
        else:
            raise ValueError(f"DataSource not supported: {dataSource}")


class AssetMapper(ABC):

    def __init__(self, asset):
        self.asset = asset["content"]

    @property
    def annotations(self):
        # Relevant Annotations
        ## columnDescriptions
        ## termTags
        ## tags
        ## schema.properties.columns
        ## friendlyName 
        return self.asset["annotations"]
    
    @property
    def tags(self):
        return self.annotations.get("tags", [])
    
    @property
    def properties(self):
        return self.asset["properties"]
    
    @property
    def name(self):
        return self.properties["name"]

class SqlServerTableMapper(AssetMapper):
    # columnDescriptions
    def _define_column_descriptions(self):
        # Check if columnDescriptions is defined
        # Get schema
        # Create objects
        # Apply description
        return None
    # documentation
    # termTags
    def entities(self):
        output = []
        server = AtlasEntity()
        database = AtlasEntity()
        schema = AtlasEntity()
        table = AtlasEntity(
            name= self.name,
            typeName="azure_sql_table",
            qualified_name=self.qualified_name(),
            guid=None
        )
        columns = []
        for col in self.schema:
            columns.append(
                AtlasEntity()
            )
        return 
    # schema
    # tags
    # friendlyName
    # descriptions
    def __init__(self, asset):
        super().__init__(asset)
        _address = self.properties["dsl"]["address"]
        self.server = _address["server"]
        self.database = _address["database"]
        self.schema = _address["schema"]
        self.table = _address["object"]
    
    def qualified_name(self, level="table"):
        output = f"mssql://{self.server}"
        if level in ["database", "schema", "table"]:
            output = output + "/" + self.database
        if level in ["schema", "table"]:
            output = output + "/" + self.schema
        if level in ["table"]:
            output = output + "/" + self.table

        return output

if __name__ == "__main__":
    with open("./test4.json", 'r') as fp:
        data = json.load(fp)
    
    output = []
    for d in data:
        try:
            _temp = AssetFactory.map_asset(d)
            output.append(_temp)
        except ValueError as e:
            print(e)
            pass
    
    print([o.annotations.keys() for o in output])
        