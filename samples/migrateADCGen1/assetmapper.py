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

    def __init__(self, asset, termMap, typeName="DataSet", columnTypeName="column"):
        self.typeName = typeName
        self.columnTypeName = columnTypeName
        self.asset = asset["content"]
        self.annotations = asset["content"].get("annotations", {})
        self.friendlyName = (
            self.annotations.get("friendlyName", {}).get("properties", {})
            .get("friendlyName", None)
        )

        self.description = ""
        _desc_list = self.annotations.get("descriptions", [])
        if len(_desc_list) > 0:
            self.description = (
                _desc_list[0].get("properties", {})
                .get("description", None)
            )

        self.term_tags = []
        for t in self.annotations.get("termTags", []):
            t_id = t.get("properties", {}).get("termId")
            if t_id and t_id in termMap:
                self.term_tags.append(termMap[t_id])

        self.experts = [e.get("properties", {}).get("expert", {}).get(
            "objectId", "") for e in self.annotations.get("experts", [])]
        # TODO: How do you support these?
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
    def column_qualified_name_pattern(self, columnName, **kwargs):
        raise NotImplementedError

    def partial_column_updates(self):
        """
        Produces a list of dicts that can be fed to a partial update. Supports
        partial updates for column descriptions.

        :return:
            List of dicts containing qualifiedName, typeName, and attributes.
            Attributes is a dict containing key: description
        :rtype: list(dict)
        """
        all_updates = []
        for colname, desc in self.columnDescriptions.items():
            column_updates = {"description": desc}
            qualified_name = self.column_qualified_name_pattern(colname)
            out = {"qualifiedName": qualified_name,
                   "typeName": self.columnTypeName, "attributes": column_updates}
            all_updates.append(out)

        return all_updates

    def partial_entity_updates(self):
        """
        Produces a dict that can be fed to a partial update. Supports
        partial updates for entity name (friendlyName from ADC) and
        description.

        :return:
            Dict containing qualifiedName, typeName, and attributes.
            Attributes is a dict containing keys: name, description based on
            whether the key was found in the original asset on ADC.
        :rtype: list(dict)
        """
        # Handles...
        # friendlyName
        # description
        updates = {}
        if self.friendlyName:
            updates["name"] = self.friendlyName
        if self.description:
            updates["description"] = self.description

        return {"qualifiedName": self.qualified_name(), "typeName": self.typeName, "attributes": updates}

    def glossary_entity_relationships(self):
        """
        Produces a list of dicts that can be fed to a relationship upload.
        Extracts from term tags.

        :return:
            List of dicts containing relationship objects to be uploaded.
        :rtype: list(dict)
        """
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

    def glossary_column_relationships(self):
        """
        Produces a list of dicts that can be fed to a relationship upload.
        Extracts from columnTermTags.

        :return:
            List of dicts containing relationship objects to be uploaded.
        :rtype: list(dict)
        """
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
                    "typeName": self.columnTypeName,
                    "uniqueAttributes": {
                        "qualifiedName": self.column_qualified_name_pattern(col)
                    }
                }
            }
            relationships.append(out)
        return relationships

    def entity(self, guid):
        # Need to take into account...
        # experts
        # friendlyName
        # description
        expert_object = None
        # KNOWN ISSUE: This will cause us to overwrite existing experts and
        # owners. No way around this because Atlas doesn't support updates to
        # complex types.
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
        if self.description:
            output.attributes.update({"description": self.description})

        return output


class SqlServerTableMapper(AssetMapper):

    def __init__(self, asset, terms, typeName="azure_sql_table", columnTypeName="azure_sql_column"):
        super().__init__(asset, terms, typeName, columnTypeName)
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

    def column_qualified_name_pattern(self, columnName):
        return self.qualified_name() + "#" + columnName


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
        print(output)
