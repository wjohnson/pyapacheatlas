import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server

# *********
# IMPORTANT
# Fill out all parameters <xxx> below before running this script
# *********

# Modify this filter if you want to add more parameters in the search
custom_filter = {
                    "and": [
                        {
                            "not": {
                                "or": [
                                    {
                                        "attributeName": "size",
                                        "operator": "eq",
                                        "attributeValue": 0
                                    },
                                    {
                                        "attributeName": "fileSize",
                                        "operator": "eq",
                                        "attributeValue": 0
                                    }
                                ]
                            }
                        },
                        {
                            "not": {
                                "classification": "MICROSOFT.SYSTEM.TEMP_FILE"
                            }
                        },
                        {
                            "not": {
                                "or": [
                                    {
                                        "entityType": "AtlasGlossaryTerm"
                                    },
                                    {
                                        "entityType": "AtlasGlossary"
                                    }
                                ]
                            }
                        }
                    ]
                }

if __name__ == "__main__":
    """
    This sample provides an example of deleting an entity through the Atlas API.
    """

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", "<TENANT_ID>"),
        client_id=os.environ.get("CLIENT_ID", "<CLIENT_ID>"),
        client_secret=os.environ.get("CLIENT_SECRET", "<CLIENT_SECRET>")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", "<PURVIEW_NAME>"),
        authentication=oauth
    )

    # When you know the GUID that you want to delete
    # response = client.delete_entity(guid="123-abc-456-def")
    # print(json.dumps(response, indent=2))

    # Replace <YOUR_FQN> with the FQN of the data source assets to be deleted
    assets_to_delete = client.discovery.search_entities(
        "<YOUR_FQN>*",
        search_filter=custom_filter
    )

    i = 0
    asset_list = ""
    with open('assets_to_delete.txt', 'w') as outfile:
        for asset in assets_to_delete:
            # Print the whole asset JSON
            # print(json.dumps(asset, indent=2))

            # Print only guid
            print(asset["id"])
            outfile.write(asset["id"] + '\n')
            i = i + 1

    print("assets_to_delete count=" + str(i))
