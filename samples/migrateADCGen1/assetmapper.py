from abc import ABC, abstractmethod
import argparse
from collections import Counter

import json

from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.util import GuidTracker


class AssetFactory():
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
        else:
            raise ValueError(f"DataSource not supported: {dataSource}")


class AssetMapper(ABC):
    """
    :param dict assets: the results section of a search query from ADC gen 1.
    :param dict(termId, termQualifiedName) termMap:
        Dict containing key of termId from ADC Gen 1 and value of the qualified
        name for the Purview glossary term (term@Glossary).
    :param str typeName: The type to be used, defaults to DataSet.
    """

    def __init__(self, asset, termMap, typeName="DataSet"):
        self.typeName = typeName
        self.asset = asset["content"]
        self.annotations = asset["content"].get("annotations", {})
        self.friendlyName = self.annotations.get("friendlyName", {}).get("properties", {}).get(
            "friendlyName", None) or self.asset.get("properties", {}).get("name", None)
        # This needs to be improved to get the real term ids
        self.term_tags = []
        for t in self.annotations.get("termTags", []):
            t_id = t.get("properties", {}).get("termId")
            if t_id and t_id in termMap:
                self.term_tags.append(termMap[t_id])

        self.experts = [e.get("properties", {}).get("expert", {}).get(
            "objectId", "") for e in self.annotations.get("experts", [])]
        self.tags = []
        self.columnTermTags = []
        for ct in self.annotations.get("columnTermTags", []):
            props = ct.get("properties", {})
            columnName = props.get("columnName", "")
            termId = props.get("termId", "")
            if termId and termId in termMap:
                self.columnTermTags.append((columnName, termMap[termId]))
        self.columnDescriptions = {}
        for cd in self.annotations.get("columnDescriptions", []):
            colobj = cd.get("properties", {})
            if "columnName" in colobj and "description" in colobj:
                self.columnDescriptions[colobj["columnName"]
                                        ] = colobj["description"]

    @abstractmethod
    def qualified_name(self):
        raise NotImplementedError

    @abstractmethod
    def column_entities(self, parent):
        # Need to take into account...
        # columnDescriptions
        # Data Type if we are creating the entity.
        raise NotImplementedError

    def glossary_relationships(self):
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

    def column_glossary_relationships(self, columnType="columns"):
        relationships = []
        # columnTermTags
        for col, term in self.columnTermTags:
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
                        "qualifiedName": self.qualified_name() + "#" + col
                    }
                }
            }
            relationships.append(out)

    def entity(self, guid):
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
            name=self.friendlyName or self.qualified_name(),
            typeName=self.typeName,
            qualified_name=self.qualified_name(),
            guid=guid,
            contacts=expert_object
        )
        return output


class SqlServerTableMapper(AssetMapper):

    def __init__(self, asset, terms, typeName="azure_sql_table"):
        super().__init__(asset, terms, typeName)
        _address = self.asset["properties"]["dsl"]["address"]
        self.server = _address["server"]
        self.database = _address["database"]
        self.schema = _address["schema"]
        self.table = _address["object"]

    def entity(self, guid):
        return super().entity(guid)

    def qualified_name(self, level="table"):
        output = f"mssql://{self.server}"
        if level in ["database", "schema", "table"]:
            output = output + "/" + self.database
        if level in ["schema", "table"]:
            output = output + "/" + self.schema
        if level in ["table"]:
            output = output + "/" + self.table

        return output

    def column_glossary_relationships(self, columnType="azure_sql_column"):
        return super().column_glossary_relationships(columnType=columnType)

    def column_entities(self, parent):
        columns = (
            self.annotations.get("schema", {})
            .get("properties", {})
            .get("columns", [])
        )

        if len(columns) == 0:
            return []

        output = []
        for col in columns:
            c_entity = AtlasEntity(
                name=col["name"],
                typeName="azure_sql_column",
                qualified_name=self.qualified_name() + "#" + col["name"],
                guid=-1,
            )
            if col["name"] in self.columnDescriptions:
                c_entity.attributes.update(
                    {"description": self.columnDescriptions[col["name"]]})
            c_entity.addRelationship(table=parent)
            output.append(c_entity)
        
        return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets")
    parser.add_argument("--terms")
    parser.add_argument("--analysis", action="store_true")
    args, _ = parser.parse_known_args()

    with open(args.terms, 'r') as fp:
        terms = json.load(fp)
        termMapping = {t["id"]: t["name"]+"@Glossary" for t in terms}

    with open(args.assets, 'r') as fp:
        data = json.load(fp)
    
    gt = GuidTracker()

    if args.analysis:
        output = dict()
        for d in data:
            content = d.get("content", {})
            ds = content.get("properties", {}).get("dataSource", {})
            sourceType = ds.get("sourceType", "SourceNotFound")
            objectType = ds.get("objectType", "TypeNotFound")
            key = sourceType + "|" + objectType

            freq = output.get(key, Counter())

            annotation_keys = Counter(
                list(content.get("annotations", {}).keys()))

            output[key] = freq + annotation_keys
        # Out of loop
        output = {k: dict(v) for k, v in output.items()}

    else:
        output = []
        for d in data:
            try:
                _temp = AssetFactory.map_asset(d, termMapping)
                output.append(_temp)
            except ValueError as e:
                print(e)
                pass
        
        test = output[0]
        print(test.qualified_name())
        table = test.entity(-1)
        print(json.dumps(table.to_json(),indent=2))
        print(json.dumps(test.column_glossary_relationships(),indent=2))
        print(json.dumps(test.glossary_relationships()  ,indent=2))
        print(json.dumps([c.to_json() for c in test.column_entities(table)]))

    print(json.dumps(output, indent=2))
