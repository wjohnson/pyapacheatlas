from collections import namedtuple

EntityField = namedtuple("EntityField",["name","isOptional"])

class WhatIfValidator():
    """
    """

    def __init__(self, type_defs):
        self.classification_defs = type_defs.get("classificationDefs", [])
        self.entity_defs = type_defs.get("entityDefs", [])
        # Create a dict of all entities by name, then find the name of all attributes and whether they are optional
        # entity_fields = {e["name"]: [{"name":attr["name"], "isOptional":attr.get("isOptional", True)} for attr in e] for e in self.entity_defs}
        entity_fields = {e["name"]:[EntityField(attr.get("name"), attr.get("isOptional")) for attr in e.get("attributeDefs", {})]  for e in self.entity_defs}
        # Adding Qualified Name to the set of valid fields as it doesn't show up in the entity type def
        self.entity_valid_fields = {k: set([field.name for field in v ]+["qualifiedName"]) for k,v in entity_fields.items()}
        # Adding Qualified Name to the set of required entity fields as it doesn't show up in the entity type def
        self.entity_required_fields = {k: set([field.name for field in v if not field.isOptional]+["qualifiedName"]) for k,v in entity_fields.items()}
        
        
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
        required_attributes = set(self.entity_required_fields[entity["typeName"]])
        missing_attributes = required_attributes.difference(current_attributes)
        if len(missing_attributes) > 0:
            return True
        else:
            return False

    def entity_has_invalid_attributes(self, entity):
        """
        Check if the entity is using attributes that are not defined on the type.

        :param dict entity:
        :param dict type_def:
        :return: Whether the entity matches the list of known entity types.
        :rtype: bool
        """
        current_attributes = set(entity.get("attributes", {}).keys())
        valid_attributes = set(self.entity_valid_fields[entity["typeName"]])
        invalid_attributes = current_attributes.difference(valid_attributes)
        if len(invalid_attributes) > 0:
            return True
        else:
            return False