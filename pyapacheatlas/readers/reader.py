from warnings import warn
from collections import OrderedDict

from ..core.util import GuidTracker
from ..core import (
    AtlasAttributeDef,
    AtlasEntity,
    ClassificationTypeDef,
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
        "ClassificationDefs": [
            "classificationName", "entityTypes", "description"
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
            A dictionary containing 'attributes' and 'relationshipAttributes'
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
        req_attribs = ["typeName", "name", "qualifiedName", "classifications", "owners", "experts"]
        existing_entities = OrderedDict()

        for row in json_rows:

            if ((row["name"] is None) or (row["typeName"] is None) or
                    (row["qualifiedName"] is None)):
                # An empty row snuck in somehow, skip it.
                continue

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
            if "experts" in row or "owners" in row and len( row.get("experts", []) + row.get("owners", []) ) > 0:
                experts = []
                owners = []
                if len(row.get("experts", []) or [])>0:
                    experts = [{"id":e} for e in row.get("experts", "").split(self.config.value_separator) if e != '']
                if len(row.get("owners", []) or [])>0:
                    owners = [{"id":o} for o in row.get("owners", "").split(self.config.value_separator) if o != '']
                entity.contacts = {"Expert": experts, "Owner": owners }

            existing_entities.update({row["qualifiedName"]: entity})

        output = {"entities": [e.to_json()
                               for e in list(existing_entities.values())]}
        return output

    def parse_entity_defs(self, json_rows):
        """
        Create an AtlasTypeDef consisting of entityDefs for the
        given json_rows.  The columns `Entity TypeName` and `Entity superTypes`
        are special and map to typeName and superTypes respectively.

        Entity TypeName must be repeated for each row that has a relevant
        attribute being defined on it. For example, if you plan on including
        five attributes for type X, you would need to have five rows and
        each row would have to fill in the Entity TypeName column.

        superTypes can be specified all in one cell (default delimiter is `;`
        and is controlled by the Reader's configuration) or across multiple
        cells. If you specify DataSet in one row for type X and hive_table
        for type X in a second row, it will result in a superType
        of `[DataSet, hive_table]`.

        :param list(dict(str,str)) json_rows:
            A list of dicts containing at least `Entity TypeName` and `name`
            that represents the metadata for a given entity type's
            attributeDefs. Extra metadata will be ignored.
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        entities = dict()
        entities_to_superTypes = dict()
        attribute_metadata_seen = set()
        output = {"entityDefs": []}

        splitter = lambda attrib: [e for e in attrib.split(self.config.value_separator) if e]
        # Required attributes
        # Get all the attributes it's expecting official camel casing
        # with the exception of "Entity TypeName"
        for row in json_rows:
            try:
                entityTypeName = row["Entity TypeName"]
            except KeyError:
                raise KeyError("Entity TypeName not found in {}".format(row))

            _ = row.pop("Entity TypeName")
            
            # If the user wants to add super types, they might be adding
            # multiple on each row. They DON'T NEED TO but they might
            entitySuperTypes = []
            if "Entity superTypes" in row:
                superTypes_string = row.pop("Entity superTypes")
                # Might return a None or empty string
                if superTypes_string:
                    entitySuperTypes = splitter(superTypes_string)
            
            # Need to add this entity to the superTypes mapping if it doesn't
            # already exist
            if entityTypeName in entities_to_superTypes:
                entities_to_superTypes[entityTypeName].extend(entitySuperTypes)
            else:
                entities_to_superTypes[entityTypeName] = entitySuperTypes
            
                
            # Update all seen attribute metadata
            columns_in_row = list(row.keys())
            attribute_metadata_seen = attribute_metadata_seen.union(
                set(columns_in_row))
            # Remove any null cells, otherwise the AttributeDefs constructor
            # doesn't use the defaults.
            for column in columns_in_row:
                if row[column] is None:
                    _ = row.pop(column)

            json_attribute_def = AtlasAttributeDef(**row).to_json()

            if entityTypeName not in entities:
                entities[entityTypeName] = []

            entities[entityTypeName].append( json_attribute_def )

        # Create the entitydefs
        for entityType in entities:
            # Handle super types by de-duping, removing Nones / empty str and
            # defaulting to ["DataSet"] if no user input super Types
            all_super_types = [t for t in set(entities_to_superTypes[entityType]) if t]
            if len(all_super_types) == 0:
                all_super_types = ["DataSet"]

            local_entity_def = EntityTypeDef(
                name=entityType,
                attributeDefs=entities[entityType],
                # Adding this as a default until I figure
                # do this from the excel / json readers.
                superTypes=all_super_types
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

    def parse_classification_defs(self, json_rows):
        """
        Create an AtlasTypeDef consisting of classificationDefs for the
        given json_rows.

        :param list(dict(str,str)) json_rows:
            A list of dicts containing at least `classificationName`.
        :return: An AtlasTypeDef with classificationDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        defs = []
        for row in json_rows:
            try:
                classificationTypeName = row["classificationName"]
            except KeyError:
                raise KeyError("classificationName not found in {}".format(row))

            _ = row.pop("classificationName")
            # Update all seen attribute metadata
            columns_in_row = list(row.keys())
            # Remove any null cells, otherwise the TypeDef constructor
            # doesn't use the defaults.
            for column in columns_in_row:
                if row[column] is None:
                    _ = row.pop(column)
            
            splitter = lambda attrib: [e for e in attrib.split(self.config.value_separator) if e]

            if "entityTypes" in row:
                row["entityTypes"] = splitter(row["entityTypes"])
            if "superTypes" in row:
                row["superTypes"] = splitter(row["superTypes"])
            if "subTypes" in row:
                row["superTypes"] = splitter(row["subTypes"])

            json_classification_def = ClassificationTypeDef(classificationTypeName, **row).to_json()

            defs.append(json_classification_def)
        
        return {"classificationDefs": defs}

    @staticmethod
    def make_template():
        """
        Generate a template for the given reader.
        """
        raise NotImplementedError
