from warnings import warn
from ...core.typedef import AtlasAttributeDef, EntityTypeDef

def to_entityDefs(json_rows):
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
    output = {"entityDefs":[]}
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
        attribute_metadata_seen = attribute_metadata_seen.union(set(columns_in_row))
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
    extra_metadata_warnings = [i for i in attribute_metadata_seen if i not in AtlasAttributeDef.propertiesEnum ]
    for extra_metadata in extra_metadata_warnings:
        warn("The attribute metadata \"{}\" is not a part of the Atlas Attribute Def and will be ignored.".format(extra_metadata))

    return output