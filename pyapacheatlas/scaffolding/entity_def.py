from ..core.typedef import *

def to_entity_def(entity_name, attributes, super_types = ["DataSet"]):
    """
    :param list(str) attributes: The attributes that should be converted into an
        entity def list of attributes.
    """
    # Take in a list of attribute names
    # Special columns: name, superTypes
    # TODO: Handling parent types already in place?
    # For each attribute, Create a default attribute def
    # Add it to the Entity Def

    attributeDefs = [AtlasAttributeDef(name=i).to_json() for i in attributes]

    entityDef = EntityTypeDef(
        name=entity_name,
        superTypes=super_types,
        attributeDefs= attributeDefs
    )

    return entityDef.to_json()

