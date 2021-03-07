import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server

if __name__ == "__main__":
    """
    This sample provides an example of deleting an entity through the Atlas API.
    """

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

    # When you know the GUID that you want to delete
    response = client.delete_entity(guid="123-abc-456-def")
    print(json.dumps(response, indent=2))

    # When you need to find multiple Guids to delete and they all
    # are the same type
    entities = client.get_entity(
        qualifiedName=["qualifiedname1", "qualifiedname2", "qualifiedname3"],
        typeName="my_type"
    )

    for entity in entities.get("entities"):
        guid = entity["guid"]
        delete_response = client.delete_entity(guid=guid)
        print(json.dumps(delete_response, indent=2))
