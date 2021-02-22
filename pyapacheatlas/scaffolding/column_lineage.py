from ..core import typedef


def column_lineage_scaffold(datasource,
                            use_column_mapping=False,
                            column_attributes=[],
                            table_attributes=[],
                            table_column_relationship_attributes=[],
                            column_lineage_attributes=[],
                            table_process_attributes=[],
                            column_lineage_process_attributes=[],
                            table_process_column_lineage_relationship_attributes=[]
                            ):
    """
    Create a base set of type definitions that adhere to the Hive Bridge
    style of Atlas Column Lineage.

    :param str datasource: The name of the data source. Acts as a prefix
        for all other type defs.
    :param bool use_column_mapping: If True, add the columnMapping attribute
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
        Attribute Defs to add to the table process column lineage
        relationship type.
    """

    src_table_columns_typeName = "{}_table_columns".format(datasource)

    # TODO: Create all combinations of datasource
    # Define {datasource}_column
    column_entity = typedef.EntityTypeDef(
        name="{}_column".format(datasource),
        superTypes=["DataSet"],
        attributeDefs=column_attributes
    )
    # Define {datasource}_table
    table_entity = typedef.EntityTypeDef(
        name="{}_table".format(datasource),
        superTypes=["DataSet"],
        attributeDefs=table_attributes,
        relationshipAttributeDefs=[],
        options={"schemaElementsAttribute": "columns"}
    )
    # Define {datasource}_table_columns relationship ()
    table_column_relationship = typedef.RelationshipTypeDef(
        name=src_table_columns_typeName,
        attributeDefs=table_column_relationship_attributes,
        relationshipCategory="COMPOSITION",
        endDef1=typedef.ParentEndDef(name="columns",typeName=table_entity.name),
        endDef2=typedef.ChildEndDef(name="table",typeName=column_entity.name)
    )

    # Define {datasource}_column_lineage
    column_lineage_process_entity = typedef.EntityTypeDef(
        name="{}_column_lineage".format(datasource),
        superTypes=["Process"],
        attributeDefs=((column_lineage_process_attributes or []) +
                       [
            typedef.AtlasAttributeDef(
                name="dependencyType",
                isOptional=True,
                valuesMinCount=1,
                valuesMaxCount=1
            ).to_json(),
            typedef.AtlasAttributeDef(
                name="expression"
            ).to_json()
        ]
        )
    )

    # Define {datasource}_process
    table_process_entity = typedef.EntityTypeDef(
        name="{}_process".format(datasource),
        superTypes=["Process"],
        attributeDefs=table_process_attributes
    )
    if use_column_mapping:
        table_process_entity.attributeDefs.append(
            typedef.AtlasAttributeDef(
                name="columnMapping"
            ).to_json()
        )

    # Define {datasource}_process_column_lineage
    table_process_column_lineage_relationship = typedef.RelationshipTypeDef(
        name="{}_process_column_lineage".format(datasource),
        relationshipCategory="COMPOSITION",
        attributeDefs=table_process_column_lineage_relationship_attributes,
        endDef1=typedef.ChildEndDef(name="query",
            typeName=column_lineage_process_entity.name,
            isLegacyAttribute=True),
        endDef2=typedef.ParentEndDef(name="columnLineages",
            typeName=table_process_entity.name,
            isLegacyAttribute=False)
    )

    # Output composite entity
    output = {
        "entityDefs": [
            column_entity.to_json(),
            table_entity.to_json(),
            column_lineage_process_entity.to_json(),
            table_process_entity.to_json()
        ],
        "relationshipDefs": [
            table_column_relationship.to_json(),
            table_process_column_lineage_relationship.to_json()
        ]
    }
    return output
