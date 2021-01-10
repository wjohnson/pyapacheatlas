import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient  # Communicate with your Atlas server

if __name__ == "__main__":
    """
    This sample provides an example of removing a classification from a given
    entity.
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
    response = client.declassify_entity(
        guid="b58fc81e-a85f-4dfc-aad1-ee33b3421b83",
        classificationName="MICROSOFT.PERSONAL.IPADDRESS"
    )
    print(json.dumps(response, indent=2))

    # When you need to find multiple classifications to delete on an entity.
    # Get all the classifications and then retrieve the "list" attribute.
    classifications = client.get_entity_classifications(
        guid="b58fc81e-a85f-4dfc-aad1-ee33b3421b83"
    )["list"]

    # For every classification, remove it.
    for classification in classifications:
        response = client.declassify_entity(
            guid="b58fc81e-a85f-4dfc-aad1-ee33b3421b83",
            classificationName=classification["typeName"]
        )
        print(response)
