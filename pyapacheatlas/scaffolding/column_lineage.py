from ..core.typedef import *

def column_lineage_scaffold(datasource,
    useColumnMapping = False,
    column_attributes = None,
    table_attributes = None,
    table_column_relationship_attributes = None,
    column_lineage_attributes = None,
    table_process_attributes = None,
    column_lineage_process_attributes = None,
    table_process_column_lineage_relationship_attributes = None
):
    """
    Create a base set of type definitions that adhere to the Hive Bridge
    style of Atlas Column Lineage.

    :param str datasource: The name of the data source. Acts as a prefix
        for all other type defs.
    :param bool useColumnMapping: If True, add the columnMapping attribute
        to the table process.
    :param list(dict), optional column_attributes: 
        Attribute Defs to add to the column entity type.
    :param list(dict), optional table_attributes: 
        Attribute Defs to add to the table entity type.
    :param list(dict), optional table_column_relationship_attributes: 
        Attribute Defs to add to the table column relationship type.
    :param list(dict), optional column_lineage_attributes: 
        Attribute Defs to add to the column lineage process entity type.
    :param list(dict), optional table_process_attributes: 
        Attribute Defs to add to the table process entity type.
    :param list(dict), optional column_lineage_process_attributes: 
        Attribute Defs to add to the column lineage process entity type.
    :param list(dict), optional table_process_column_lineage_relationship_attributes:
        Attribute Defs to add to the table process column lineage relationship type.
    """
    # TODO: Create all combinations of datasource
    # Define {datasource}_column
    column_entity = EntityTypeDef(
        name="{}_column".format(datasource),
        superTypes=["DataSet"],
        attributeDefs=column_attributes
    )
    # Define {datasource}_table
    table_entity = EntityTypeDef(
        name="{}_table".format(datasource),
        superTypes=["DataSet"],
        attributeDefs=table_attributes
        # TODO: Add the relationship attribute to support scaffolding to upload
    )
    # Define {datasource}_table_columns relationship ()
    table_column_relationship = RelationshipTypeDef(
        name="{}_table_columns".format(datasource),
        attributeDefs=table_column_relationship_attributes,
        relationshipCategory = "COMPOSITION",
        endDef1 = {
            "type": table_entity.name,
            "name": "columns",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": False
            },
        endDef2 = {
            "type": column_entity.name,
            "name": "table",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": False
        }
    )

    # Define {datasource}_column_lineage
    column_lineage_process_entity = EntityTypeDef(
        name="{}_column_lineage".format(datasource),
        attributeDefs=column_lineage_process_attributes,
        superTypes=["Process"],
        attributes=[
            {
            "name": "dependencyType",
            "typeName": "string",
            "isOptional": False,
            "cardinality": "SINGLE",
            "valuesMinCount": 1,
            "valuesMaxCount": 1,
            "isUnique": False,
            "isIndexable": False,
            "includeInNotification": False
            },
            {
            "name": "expression",
            "typeName": "string",
            "isOptional": True,
            "cardinality": "SINGLE",
            "valuesMinCount": 0,
            "valuesMaxCount": 1,
            "isUnique": False,
            "isIndexable": False,
            "includeInNotification": False
            }
        ]
    )

    # Define {datasource}_process
    table_process_entity = EntityTypeDef(
        name="{}_process".format(datasource),
        superTypes=["Process"],
        attributeDefs=table_process_attributes
    )
    if useColumnMapping:
        table_process_entity.attributeDefs.append(
            {
            "name": "columnMapping",
            "typeName": "string",
            "cardinality": "SINGLE",
            "isIndexable": False,
            "isOptional": True,
            "isUnique": False
            }
        )

    # Define {datasource}_process_column_lineage
    table_process_column_lineage_relationship = RelationshipTypeDef(
        name="{}_process_column_lineage".format(datasource),
        relationshipCategory = "COMPOSITION",
        attributeDefs=table_process_column_lineage_relationship_attributes,
        endDef1 = {
            "type": column_lineage_process_entity.name,
            "name": "query",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": True
            },
        endDef2 = {
            "type": table_process_entity.name,
            "name": "columnLineages",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": False
        }
    )


    # Output composite entity
    output = {
        "entityDefs":[
            column_entity.to_json(),
            table_entity.to_json(),
            column_lineage_process_entity.to_json(),
            table_process_entity.to_json()
        ],
        "relationshipDefs":[
            table_column_relationship.to_json(),
            table_process_column_lineage_relationship.to_json()
        ]
    }
    return output