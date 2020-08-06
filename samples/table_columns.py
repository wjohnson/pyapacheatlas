import json

from pyapacheatlas.core.typedef import EntityTypeDef, RelationshipTypeDef


if __name__ == "__main__":
    """
    This sample provides an example of generating the bare
    minimum table and columns scaffolding with a relationship
    definition between the table and column types.
    """    
    datasource = "samplesource"

    src_table_columns_typeName = "{}_table_columns".format(datasource)

    # TODO: Create all combinations of datasource
    # Define {datasource}_column
    column_entity = EntityTypeDef(
        name="{}_column".format(datasource),
        superTypes=["DataSet"],
    )
    # Define {datasource}_table
    table_entity = EntityTypeDef(
        name="{}_table".format(datasource),
        superTypes=["DataSet"],
        relationshipAttributeDefs=[],
        options={"schemaElementsAttribute": "columns"}
    )
    # Define {datasource}_table_columns relationship ()
    table_column_relationship = RelationshipTypeDef(
        name=src_table_columns_typeName,
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

    output = {
            "entityDefs":[
                column_entity.to_json(),
                table_entity.to_json()
            ],
            "relationshipDefs":[
                table_column_relationship.to_json(),
            ]
        }
    print(json.dumps(output))