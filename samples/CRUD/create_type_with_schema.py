import os
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import (
    AtlasAttributeDef,
    AtlasEntity,
    PurviewClient,
    RelationshipTypeDef
)
from pyapacheatlas.core.typedef import EntityTypeDef
from pyapacheatlas.core.util import GuidTracker


if __name__ == "__main__":
    """
    This sample provides shows how to create custom type definitions and
    use a relationship to create a table/columns connection. Lastly it
    creates entities to demonstrate using the custom types with the
    relationship.
    """
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    # Create Type Definitions and Relationship Definition
    # The Relationship defines the table / columns connection between
    # the entities.

    column_entity_def = EntityTypeDef(
        name="pyapacheatlas_demo_column",
        superTypes=["DataSet"],
        attributeDefs=[
            AtlasAttributeDef("data_type", typeName="string", isOptional=False)
        ]
    )

    table_entity_def = EntityTypeDef(
        name="pyapacheatlas_demo_table",
        superTypes=["DataSet"],
        relationshipAttributeDefs=[],
        options={"schemaElementsAttribute": "columns"}
    )

    # Creating a relationship type definition requires defining an endDef1
    # (the parent) and endDef2 (the child). When using a "COMPOSITION"
    # category (e.g. the column cannot exist without a table), endDef1 must
    # have isContainer set to True and endDef2's # isContainer is set to false.
    table_column_relationship = RelationshipTypeDef(
        name="pyapacheatlas_table_column_relationship",
        relationshipCategory="COMPOSITION",
        endDef1={
            "type": table_entity_def.name,
            "name": "columns",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": False,
        },
        endDef2={
            "type": column_entity_def.name,
            "name": "table",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": False
        }
    )

    # Upload the results 
    upload_results = client.upload_typedefs(
        entityDefs=[column_entity_def, table_entity_def],
        relationshipDefs=[table_column_relationship],
        force_update=True
    )

    # With all the types and relationships defined, we can create entities.
    # We can use a GuidTracker to always get a unique negative number
    gt = GuidTracker()

    table_entity = AtlasEntity(
        name="sample_table",
        qualified_name="pyapacheatlas://sample_tablepyapacheatlas_custom_type",
        typeName="pyapacheatlas_demo_table",
        guid=gt.get_guid()
    )

    # Add two columns. They must include the "relationshipAttribute" attribute.
    column01 = AtlasEntity(
        name="column01",
        typeName="pyapacheatlas_demo_column",
        qualified_name="pyapacheatlas://sample_tablepyapacheatlas_custom_type@column01",
        attributes={
            "data_type": "string",
            "description": "This is the first column."
        },
        guid=gt.get_guid()
    )
    column02 = AtlasEntity(
        name="column02",
        typeName="pyapacheatlas_demo_column",
        qualified_name="pyapacheatlas://sample_tablepyapacheatlas_custom_type@column02",
        attributes={
            "data_type": "int",
            "description": "This is the second column."
        },
        guid=gt.get_guid()
    )
    
    # Add the "table" relationship attribute to your column entities
    column01.addRelationship(table=table_entity)
    column02.addRelationship(table=table_entity)

    
    upload_results = client.upload_entities(
        batch=[table_entity, column01, column02]
    )

    print(json.dumps(upload_results, indent=2))
