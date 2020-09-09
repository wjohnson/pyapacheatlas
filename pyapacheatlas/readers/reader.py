from warnings import warn

from ..core.util import GuidTracker
from ..core import (
    AtlasAttributeDef,
    AtlasEntity, 
    AtlasProcess,
    EntityTypeDef
)

from .lineagemixin import LineageMixIn
from .util import *

class ReaderConfiguration():

    def __init__(self, **kwargs):
        super().__init__()
        self.value_separator = kwargs.get('value_separator', ';')
        self.source_prefix = kwargs.get(
            "source_prefix", "Source")
        self.target_prefix = kwargs.get(
            "target_prefix", "Target")
        self.process_prefix = kwargs.get(
            "process_prefix", "Process")
        self.column_transformation_name = kwargs.get(
            "column_transformation_name", "Transformation")


class Reader(LineageMixIn):
    TEMPLATE_HEADERS = {
        "ColumnsLineage": [
            "Target Table", "Target Column", "Target Classifications",
            "Source Table", "Source Column", "Source Classifications",
            "Transformation"
        ],
        "TablesLineage": [
            "Target Table", "Target Type", "Target Classifications",
            "Source Table", "Source Type", "Source Classifications",
            "Process Name", "Process Type"
        ],
        "EntityDefs": [
            "Entity TypeName", "name", "description",
            "isOptional", "isUnique", "defaultValue",
            "typeName", "displayName", "valuesMinCount",
            "valuesMaxCount", "cardinality", "includeInNotification",
            "indexType", "isIndexable"
        ],
        "BulkEntities": [
            "typeName", "name", "qualifiedName", "classifications"
        ]
    }

    def __init__(self, configuration, guid=-1000):
        """
        Creates the base Reader with functionality that supports python dicts.

        :param configuration:
            A list of dicts containing at least `Entity TypeName` and `name`
        :type configuration: 
            :class:`~pyapacheatlas.readers.reader.ReaderConfiguration`
        :param int guid:
            A negative integer to use as the starting counter for entities
            created by this reader.
        """
        super().__init__()
        self.config = configuration
        self.guidTracker = GuidTracker(guid)

    def parse_bulk_entities(self, json_rows):
        """
        Create an AtlasTypeDef consisting of entities and their attributes for the given json_rows.

        :param list(dict(str,str)) json_rows:
            A list of dicts containing at least `Entity TypeName` and `name`
            that represents the metadata for a given entity type's attributeDefs.
            Extra metadata will be ignored.
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        # For each row,
        # Extract the
        # Extract any additional attributes
        req_attribs = ["typeName", "name", "qualifiedName", "classifications"]
        output = {"entities": []}
        for row in json_rows:
            # Remove any cell with a None / Null attribute
            # Remove the required attributes so they're not double dipping.
            custom_attributes = {
                k: v for k, v in row.items()
                if k not in req_attribs and v is not None
            }
            entity = AtlasEntity(
                name=row["name"],
                typeName=row["typeName"],
                qualified_name=row["qualifiedName"],
                guid=self.guidTracker.get_guid(),
                attributes=custom_attributes,
                classifications=string_to_classification(
                    row["classifications"],
                    sep=self.config.value_separator
                )
            ).to_json()
            output["entities"].append(entity)
        return output

    def parse_entity_defs(self, json_rows):
        """
        Create an AtlasTypeDef consisting of entityDefs for the given json_rows.

        :param list(dict(str,str)) json_rows:
            A list of dicts containing at least `Entity TypeName` and `name`
            that represents the metadata for a given entity type's attributeDefs.
            Extra metadata will be ignored.
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        entities = dict()
        attribute_metadata_seen = set()
        output = {"entityDefs": []}
        # Required attributes
        # Get all the attributes it's expecting official camel casing
        # with the exception of "Entity TypeName"
        for row in json_rows:
            try:
                entityTypeName = row["Entity TypeName"]
            except KeyError:
                raise KeyError("Entity TypeName not foud in {}".format(row))

            _ = row.pop("Entity TypeName")
            # Update all seen attribute metadata
            columns_in_row = list(row.keys())
            attribute_metadata_seen = attribute_metadata_seen.union(
                set(columns_in_row))
            # Remove any null cells, otherwise the AttributeDefs constructor
            # doesn't use the defaults.
            for column in columns_in_row:
                if row[column] is None:
                    _ = row.pop(column)

            json_entity_def = AtlasAttributeDef(**row).to_json()

            if entityTypeName not in entities:
                entities[entityTypeName] = []

            entities[entityTypeName].append(json_entity_def)

        # Create the entitydefs
        for entityType in entities:
            local_entity_def = EntityTypeDef(
                name=entityType,
                attributeDefs=entities[entityType]
            ).to_json()
            output["entityDefs"].append(local_entity_def)

        # Extra attribute metadata (e.g. extra columns / json entries) are ignored.
        # Warn the user that this metadata will be ignored.
        extra_metadata_warnings = [
            i for i in attribute_metadata_seen if i not in AtlasAttributeDef.propertiesEnum]
        for extra_metadata in extra_metadata_warnings:
            warn(("The attribute metadata \"{}\" is not a part of the Atlas" +
                  " Attribute Def and will be ignored.").format(
                extra_metadata))

        return output
    

    @staticmethod
    def make_template():
        raise NotImplementedError

    