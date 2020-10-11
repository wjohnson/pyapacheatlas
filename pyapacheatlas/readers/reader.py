from warnings import warn
from collections import OrderedDict

from ..core.util import GuidTracker
from ..core import (
    AtlasAttributeDef,
    AtlasEntity,
    EntityTypeDef
)

from .lineagemixin import LineageMixIn
from . import util as reader_util


class ReaderConfiguration():
    """
    A base configuration for the Reader class.  Allows you to customize
    headers with a source_prefix, target_prefix, and process_prefix for
    parsing table and column lineages.
    """

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
            "column_transformation_name", "transformation")


class Reader(LineageMixIn):
    """
    The base Reader with functionality that supports python dicts.
    """
    TEMPLATE_HEADERS = {
        "ColumnsLineage": [
            "Target table", "Target column", "Target classifications",
            "Source table", "Source column", "Source classifications",
            "transformation"
        ],
        "TablesLineage": [
            "Target table", "Target type", "Target classifications",
            "Source table", "Source type", "Source classifications",
            "Process name", "Process type"
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
        ],
        "UpdateLineage": [
            "Target typeName", "Target qualifiedName", "Source typeName",
            "Source qualifiedName", "Process name", "Process qualifiedName",
            "Process typeName"
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

    def _organize_attributes(self, row, existing_entities, ignore=[]):
        """
        Organize the row entries into a distinct set of attributes and
        relationshipAttributes.

        :param dict(str,str) row:
            A dict representing the input rows.
        :param existing_entities:
            A list of existing atlas entities that will be used to infer
            any relationship attributes.
        :type existing_entities:
            dict(str, `:class:~pyapacheatlas.core.entity.AtlasEntity`)
        :param list(str) ignore:
            A set of keys to ignore and omit from the returned dict.
        :return:
            A dictionary containing 'ttributes' and 'relationshipAttributes'
        :rtype: dict(str, dict(str,str))
        """
        output = {"attributes": {}, "relationshipAttributes": {}}
        for k, v in row.items():
            # Remove the required attributes so they're not double dipping.
            if k in ignore:
                continue
            # Remove any cell with a None / Null attribute
            elif v is None:
                continue
            # If the Attribute key starts with [Relationship]
            # Move it to the relation
            elif k.startswith("[Relationship]"):
                cleaned_key = k.replace("[Relationship]", "").strip()
                # Assuming that we can find this in an existing entity
                try:
                    min_reference = existing_entities[v].to_json(minimum=True)
                # LIMITATION: We must have already seen the relationship
                # attribute to be certain it can be looked up.
                except KeyError:
                    raise KeyError(
                        f"The entity {v} should be listed before {row['qualifiedName']}."
                    )
                output["relationshipAttributes"].update(
                    {cleaned_key: min_reference}
                )
            else:
                output["attributes"].update({k: v})

        return output

    def parse_bulk_entities(self, json_rows):
        """
        Create an AtlasTypeDef consisting of entities and their attributes
        for the given json_rows.

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
        existing_entities = OrderedDict()

        for row in json_rows:

            _attributes = self._organize_attributes(
                row,
                existing_entities,
                req_attribs
            )

            entity = AtlasEntity(
                name=row["name"],
                typeName=row["typeName"],
                qualified_name=row["qualifiedName"],
                guid=self.guidTracker.get_guid(),
                attributes=_attributes["attributes"],
                classifications=reader_util.string_to_classification(
                    row["classifications"],
                    sep=self.config.value_separator
                ),
                relationshipAttributes=_attributes["relationshipAttributes"]
            )
            existing_entities.update({row["qualifiedName"]: entity})

        output = {"entities": [e.to_json()
                               for e in list(existing_entities.values())]}
        return output

    def parse_entity_defs(self, json_rows):
        """
        Create an AtlasTypeDef consisting of entityDefs for the
        given json_rows.

        :param list(dict(str,str)) json_rows:
            A list of dicts containing at least `Entity TypeName` and `name`
            that represents the metadata for a given entity type's
            attributeDefs. Extra metadata will be ignored.
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

        # Extra attribute metadata (e.g. extra columns / json entries)
        # are ignored. Warn the user that this metadata will be ignored.
        extra_metadata_warnings = [
            i for i in attribute_metadata_seen if i not in AtlasAttributeDef.propertiesEnum]
        for extra_metadata in extra_metadata_warnings:
            warn(("The attribute metadata \"{}\" is not a part of the Atlas" +
                  " Attribute Def and will be ignored.").format(
                extra_metadata))

        return output

    @staticmethod
    def make_template():
        """
        Generate a template for the given reader.
        """
        raise NotImplementedError
