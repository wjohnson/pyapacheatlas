from ..core.typedef import *

def column_lineage_scaffold(datasource,
    column_attributes = None,
    table_attributes = None,
    table_column_relationship_attributes = None,
    column_lineage_attributes = None,
    table_process_attributes = None,
    useColumnMapping = False,
    column_lineage_process_attributes = None
):
    # TODO: Create all combinations of datasource
    # Define {datasource}_column
    column_entity = EntityTypeDef(
        name="{}_column".format(datasource),
        superTypes=["DataSet"]
    )
    # Define {datasource}_table
    table_entity = EntityTypeDef(
        name="{}_table".format(datasource),
        superTypes=["DataSet"]
    )
    # Define {datasource}_table_columns relationship ()
    table_column_relationship = RelationshipTypeDef(
        name="{}_table_columns".format(datasource),
        endDef1 = table_entity.name,
        endDef2 = column_entity.name
    )

    # Define {datasource}_column_lineage
    column_lineage_process_entity = EntityTypeDef(
        name="{}_column_lineage".format(datasource),
        superTypes=["Process"],
    )

    # Define {datasource}_process
    table_process_entity = EntityTypeDef(
        name="{}_process".format(datasource),
        superTypes=["Process"],
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