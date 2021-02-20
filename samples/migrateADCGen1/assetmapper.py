from abc import ABC, abstractproperty
import json

class AssetMapper(ABC):

    def __init__(self, asset):
        self.asset = asset["content"]
    
    @abstractproperty
    def qualified_name(self):
        raise NotImplementedError

    @abstractproperty
    def relationships(self):
        raise NotImplementedError

    @property
    def annotations(self):
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
    
    def __init__(self, asset):
        super().__init__(asset)
        _address = self.properties["dsl"]["address"]
        self.server = _address["server"]
        self.database = _address["database"]
        self.schema = _address["schema"]
        self.table = _address["object"]
    
    @property
    def qualified_name(self):
        return f"mssql://{self.server}/{self.database}/{self.schema}/{self.table}"
    
    @property
    def relationships(self):
        output = {
            "columns": self.annotations.get("schema", {}).get("properties", {}).get("columns", []),
            "dboSchema": f"mssql://{self.server}/{self.database}/{self.schema}"
        }
        return output

    

if __name__ == "__main__":
    with open("./test.json", 'r') as fp:
        data = json.load(fp)
    mapped = SqlServerTableMapper(data[5])
    print(mapped.qualified_name)
    print(mapped.relationships)
    