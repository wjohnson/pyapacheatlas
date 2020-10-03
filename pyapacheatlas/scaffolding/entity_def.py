from ..core import typedef


def to_entity_def(entity_name, attributes, super_types=["DataSet"]):
    """
    :param str entity_name: The name of the entity definition to create.
    :param list(str) attributes:
        The attributes that should be converted into an
        entity def list of attributes.
    :param list(str) super_types: The super types to inherit from.

    :return: An entity definition with the provided attributes and the default
        settings of attributes as defined in
        :class:`~pyapacheatlas.core.typedef.AtlasAttributeDef`.
    :rtype: dict
    """
    # Take in a list of attribute names
    # Special columns: name, superTypes
    # TODO: Handling parent types already in place?
    # For each attribute, Create a default attribute def
    # Add it to the Entity Def

    attributeDefs = [
        typedef.AtlasAttributeDef(name=i).to_json() for i in attributes]

    entityDef = typedef.EntityTypeDef(
        name=entity_name,
        superTypes=super_types,
        attributeDefs=attributeDefs
    )

    return entityDef.to_json()
