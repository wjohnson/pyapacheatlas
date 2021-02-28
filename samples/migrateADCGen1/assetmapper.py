from abc import ABC, abstractmethod
import argparse
from collections import Counter

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

    def __init__(self, asset, typeName="DataSet"):
        self.typeName = typeName
        self.asset = asset["content"]
        self.annotations = asset["content"].get("annotations", {})
        self.friendlyName = self.annotations.get("friendlyName", None) or self.asset.get("properties", {}).get("name", None)
        # This needs to be improved to get the real term ids
        self.term_tags = [t.get("properties", {}).get("termId", "") for t in self.annotations.get("termTags", [])]
        self.experts = [e.get("properties", {}).get("expert", {}).get("objectId", "") for e in self.annotations.get("experts", [])]
        self.tags = []
        self.columnTermTags = []
        for ct in self.annotations.get("columnTermTags", []):
            props = ct.get("properties", {})
            columnName = props.get("columnName", "")
            termId = props.get("termId", "")
            self.columnTermTags.append( (columnName, termId) )

    @abstractmethod
    def qualified_name(self):
        raise NotImplementedError

    @abstractmethod
    def column_entities(self):
        # Need to take into account...
        # columnTermTags
        raise NotImplementedError

    def relationship(self):
        # term_tags
        relationships = []
        for term in self.term_tags:
            out = {
                "typeName": "AtlasGlossarySemanticAssignment",
                "attributes": {},
                "end1": {
                    "typeName": "AtlasGlossaryTerm",
                    "uniqueAttributes": {
                        "qualifiedName": term
                    }
                },
                "end2": {
                    "typeName": self.typeName,
                    "uniqueAttributes": {
                        "qualifiedName": self.qualified_name()
                    }
                }
            }
            relationships.append(out)
        
        return relationships
    

    def entity(self):
        # Need to take into account...
        # experts
        # friendlyName
        expert_object = None
        if len(self.experts) > 0:
            expert_object = {
                "Expert": [{"id": aadObjectid} for aadObjectid in self.experts],
                "Owner": []
            }

        output = AtlasEntity(
            name= self.friendlyName or self.qualified_name(),
            typeName=typeName,
            qualified_name=self.qualified_name(),
            guid=None,
            contacts = expert_object
        )
        return output


class SqlServerTableMapper(AssetMapper):
    
    def entity(self, typeName="azure_sql_table"):
        return super.entity(typeName="azure_sql_table")
    
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets")
    parser.add_argument("--analysis", action="store_true")
    args, _ = parser.parse_known_args()

    with open(args.assets, 'r') as fp:
        data = json.load(fp)

    if args.analysis:
        output = dict()
        for d in data:
            content = d.get("content", {})
            ds = content.get("properties", {}).get("dataSource", {})
            sourceType = ds.get("sourceType","SourceNotFound")
            objectType = ds.get("objectType","TypeNotFound")
            key = sourceType + "|" + objectType

            freq = output.get(key, Counter())

            annotation_keys = Counter(list(content.get("annotations", {}).keys()))

            output[key] = freq + annotation_keys
        # Out of loop
        output = {k: dict(v) for k,v in output.items()}


    else:
        output = []
        for d in data:
            try:
                _temp = AssetFactory.map_asset(d)
                output.append(_temp)
            except ValueError as e:
                print(e)
                pass
    
    print(json.dumps(output,indent=2))
            