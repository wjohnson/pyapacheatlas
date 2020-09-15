import argparse
import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient  # Communicate with your Atlas server
from pyapacheatlas.core import EntityTypeDef, RelationshipTypeDef

if __name__ == "__main__":
    """
    This sample provides an example of generating the bare
    minimum table and columns scaffolding with a relationship
    definition between the table and column types.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix",
                        help="The prefix for the table, columns, and relationship types.")
    args = parser.parse_args()
    datasource = args.prefix

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = AtlasClient(
        endpoint_url=os.environ.get("ENDPOINT_URL", ""),
        authentication=oauth
    )

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
        relationshipCategory="COMPOSITION",
        endDef1={
            "type": table_entity.name,
            "name": "columns",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": False
        },
        endDef2={
            "type": column_entity.name,
            "name": "table",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": False
        }
    )

    output = {
        "entityDefs": [
            column_entity.to_json(),
            table_entity.to_json()
        ],
        "relationshipDefs": [
            table_column_relationship.to_json(),
        ]
    }
    print(json.dumps(output, indent=2))

    input(">>>>Ready to upload?")

    upload_results = client.upload_typedefs(output)

    print(json.dumps(upload_results, indent=2))
