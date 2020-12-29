import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient, AtlasEntity, AtlasProcess

if __name__ == "__main__":
    """
    This sample provides an example of reading an existing entity
    through the rest api / pyapacheatlas classes.

    You need either the Guid of the entity or the qualified name and type name.

    The schema of the response follows the /v2/entity/bulk GET operation
    even if you are requesting only one entity by Guid.
    https://atlas.apache.org/api/v2/json_AtlasEntitiesWithExtInfo.html

    The response of get_entity will be a dict that has an "entities" key
    that contains a list of the entities you requested.
    """

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

    # When you know the GUID that you want to get
    response = client.get_entity(guid="123-abc-456-def")
    print(json.dumps(response, indent=2))

    # When you need to find multiple Guids and they all are the same type
    entities = client.get_entity(
        qualifiedName=["qualifiedname1", "qualifiedname2", "qualifiedname3"],
        typeName="my_type"
    )

    for entity in entities.get("entities"):
        print(json.dumps(entity, indent=2))
