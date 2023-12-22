import json
import os

from azure.identity import AzureCliCredential
from pyapacheatlas.core import PurviewClient

if __name__ == "__main__":
    """
    This sample demonstrates how to use the Purview GraphQL endpoint.

    For more sample queries see: https://learn.microsoft.com/en-us/purview/tutorial-graphql-api
    """
    cred = AzureCliCredential()
    client = PurviewClient(
            account_name=os.environ.get("PURVIEW_NAME", "InsertDefaultPurviewAccountName"),
            authentication=cred
        )

    graphql_query = """
    query {
        entities(where: { guid: ["a8bd4ed2-3c2a-4745-b7bb-68f6f6f60000"] }) {
            guid
            createTime
            updateTime
            typeName
            attributes
            name
            qualifiedName
            description
        }
    }
    """

    # Call the query endpoint with your GraphQL query
    resp = client.graphql.query(graphql_query)

    # Iterate over the results inside of the data and entities objects
    for entity in resp["data"]["entities"]:
        print(json.dumps(entity))
