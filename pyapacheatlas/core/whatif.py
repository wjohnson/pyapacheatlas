from collections import namedtuple
import json
import warnings

EntityField = namedtuple("EntityField", ["name", "isOptional"])


class WhatIfValidator():
    """
    Provides a simple way to validate that your entities will successfully
    upload.  Provides functions to validate the type, check if required
    attributes are missing, and check if superfluous attributes are included.

    :param dict type_defs:
        The list of type definitions to be validated against.  Should be
        in the form of an AtlasTypeDef composite wrapper.
    :param list(dict) existing_entities:
        The existing entities that should be validated against.
    """
    ASSET_ATTRIBUTES = ["name", "description", "owner"]
    REFERENCABLE_ATTRIBUTES = ["qualifiedName"]

    ATLAS_MODEL = {
        "ASSET": ["name", "description", "owner"],
        "REFERENCABLE": ["qualifiedName"],
        "PROCESS": (["inputs", "outputs"] +
                    ASSET_ATTRIBUTES + REFERENCABLE_ATTRIBUTES),
        "DATASET": ASSET_ATTRIBUTES + REFERENCABLE_ATTRIBUTES,
        "INFRASTRUCTURE": ASSET_ATTRIBUTES + REFERENCABLE_ATTRIBUTES
    }

    def __init__(self, type_defs={}, existing_entities=[]):
        if len(type_defs) == 0 and len(existing_entities) == 0:
            warnings.warn(
                "WARNING: Provided type_defs and existing_entities are empty.  All validations will pass.")

        self.classification_defs = type_defs.get("classificationDefs", [])
        self.entity_defs = type_defs.get("entityDefs", [])
        # Create a dict of all entities by name, then find the name of all
        # attributes and whether they are optional
        entity_fields = {}
        for e in self.entity_defs:
            entity_fields[e["name"]] = []
            for attr in e.get("attributeDefs", []):
                ef = EntityField(attr.get("name"), attr.get("isOptional"))
                entity_fields[e["name"]].append(ef)

        # Adding Qualified Name to the set of valid fields as it doesn't
        # show up in the entity type def
        self.entity_valid_fields = {k: set(
            [field.name for field in v] + ["qualifiedName"])
            for k, v in entity_fields.items()}
        # Adding Qualified Name to the set of required entity
        # fields as it doesn't show up in the entity type def
        self.entity_required_fields = {
            k: set([field.name for field in v if not field.isOptional] + [
                "qualifiedName"]) for k, v in entity_fields.items()
        }

        self.existing_entities = set(
            [e.get("attributes", {}).get("qualifiedName") for
             e in existing_entities])

        self.enum_defs = type_defs.get("enumDefs", [])
        self.relationship_defs = type_defs.get("relationshipDefs", [])
        self.struct_defs = type_defs.get("structDefs", [])

    def entity_type_exists(self, entity):
        """
        Validate that the entity's type is an actual entity definition.

        :param dict entity:
        :return: Whether the entity matches the list of known entity types.
        :rtype: bool
        """
        current_type = entity["typeName"]
        if current_type in self.entity_valid_fields:
            return True
        else:
            return False

    def entity_missing_attributes(self, entity):
        """
        Check if the entity is missing required attributes.

        :param dict entity:
        :param dict type_def:
        :return: Whether the entity matches the list of known entity types.
        :rtype: bool
        """

        current_attributes = set(entity.get("attributes", {}).keys())
        required_attributes = set(
            self.entity_required_fields[entity["typeName"]])
        missing_attributes = required_attributes.difference(current_attributes)
        if len(missing_attributes) > 0:
            return missing_attributes
        else:
            return False

    def entity_has_invalid_attributes(self, entity):
        """
        Check if the entity is using attributes that are not defined
        on the type.

        :param dict entity:
        :return: Whether the entity matches the list of known entity types.
        :rtype: bool
        """
        current_attributes = set(entity.get("attributes", {}).keys())
        valid_attributes = set(self.entity_valid_fields[entity["typeName"]])
        # Append inherited attributes:
        _entity_type = entity["typeName"]
        # Assuming only one entity matches and only one super type
        super_type = [e["superTypes"]
                      for e in self.entity_defs
                      if e["name"] == _entity_type][0][0].upper()
        if super_type in self.ATLAS_MODEL:
            valid_attributes = valid_attributes.union(
                self.ATLAS_MODEL[super_type])
        invalid_attributes = current_attributes.difference(valid_attributes)

        if len(invalid_attributes) > 0:
            return invalid_attributes
        else:
            return False

    def entity_would_overwrite(self, entity):
        """
        Based on the qualified name attributes, does the provided
        entity exist in the entities provided to the What If Validator?

        :param dict entity:
        :return: Whether the entity matches an existing entity.
        :rtype: bool
        """
        current_qualifiedName = entity.get(
            "attributes", {}).get("qualifiedName")
        if current_qualifiedName is None:
            raise KeyError("Entity has no qualifiedName:\n{}".format(
                json.dumps(entity, indent=1)))

        if current_qualifiedName in self.existing_entities:
            return True
        else:
            return False

    def validate_entities(self, entities):
        """
        Provide a report of invalid entities.  Includes TypeDoesNotExist,
        UsingInvalidAttributes, and MissingRequiredAttributes.

        :param list(dict) entities: A list of entities to validate.
        :return: A dictionary containing counts values for the above values.
        :rtype: dict
        """
        report = {"TypeDoesNotExist": [], "UsingInvalidAttributes": {},
                  "MissingRequiredAttributes": {}}

        for entity in entities:
            if not self.entity_type_exists(entity):
                report["TypeDoesNotExist"].append(entity["guid"])
                # If it's an invalid type, we have to skip over the rest
                # of this
                continue

            using_invalid = self.entity_has_invalid_attributes(entity)
            is_missing = self.entity_missing_attributes(entity)
            cur_guid = entity["guid"]
            if using_invalid:
                report["UsingInvalidAttributes"][cur_guid] = using_invalid

            if is_missing:
                report["MissingRequiredAttributes"][cur_guid] = is_missing

        output = {
            "counts": {k: len(v) for k, v in report.items()},
            "values": report
        }
        output.update({"total": sum(output["counts"].values())})

        return output
