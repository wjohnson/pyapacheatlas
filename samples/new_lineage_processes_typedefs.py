import argparse
import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server
from pyapacheatlas.core import EntityTypeDef, RelationshipTypeDef


if __name__ == "__main__":
    """
    This sample provides an example of generating the bare
    minimum table and columns scaffolding with a relationship
    definition between the table and column types.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix",
                        help="The prefix for the table and columns lineage types.")
    args = parser.parse_args()
    datasource = args.prefix

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    src_table_columns_typeName = "{}_table_columns".format(datasource)

    # Define {datasource}_column_lineage
    column_lineage_process_entity = EntityTypeDef(
        name="{}_column_lineage".format(datasource),
        superTypes=["Process"],
        attributeDefs=(
            [
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
    )

    # Define {datasource}_process
    table_process_entity = EntityTypeDef(
        name="{}_process".format(datasource),
        superTypes=["Process"],
        attributeDefs=[
            {
                "name": "columnMapping",
                "typeName": "string",
                "cardinality": "SINGLE",
                "isIndexable": False,
                "isOptional": True,
                "isUnique": False
            }
        ]
    )

    # Define {datasource}_process_column_lineage
    table_process_column_lineage_relationship = RelationshipTypeDef(
        name="{}_process_column_lineage".format(datasource),
        relationshipCategory="COMPOSITION",
        endDef1={
            "type": column_lineage_process_entity.name,
            "name": "query",
            "isContainer": False,
            "cardinality": "SINGLE",
            "isLegacyAttribute": True
        },
        endDef2={
            "type": table_process_entity.name,
            "name": "columnLineages",
            "isContainer": True,
            "cardinality": "SET",
            "isLegacyAttribute": False
        }
    )

    # Output composite entity
    output = {
        "entityDefs": [
            column_lineage_process_entity.to_json(),
            table_process_entity.to_json()
        ],
        "relationshipDefs": [
            table_process_column_lineage_relationship.to_json()
        ]
    }
    print(json.dumps(output, indent=2))

    input(">>>>Ready to upload?")

    upload_results = client.upload_typedefs(output)

    print(json.dumps(upload_results, indent=2))
