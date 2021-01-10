import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess
from pyapacheatlas.core.util import AtlasException

if __name__ == "__main__":
    """
    This sample provides an example of reading an existing entity's
    classifications through the rest api / pyapacheatlas classes.

    You need the Guid of the entity and the .

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
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    # For a given guid, check if a given classification type is applied
    # If it's not, an AtlasException is thrown.
    try:
        single_class_check = client.get_entity_classification(
            guid="b58fc81e-a85f-4dfc-aad1-ee33b3421b87",
            classificationName="MICROSOFT.PERSONAL.IPADDRESS"
        )
        print(json.dumps(single_class_check, indent=2))
    except AtlasException as e:
        print("The provided classification was not found on the provied entity.")
        print(e)

    # You can also get ALL of the classifications from a given entity
    all_class_check = client.get_entity_classifications(
        guid="b58fc81e-a85f-4dfc-aad1-ee33b3421b83"
    )
    print(json.dumps(all_class_check, indent=2))
