import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasClassification, AtlasEntity, AtlasProcess
from pyapacheatlas.core.util import AtlasException

if __name__ == "__main__":
    """
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

    # Create an entity
    # You must provide a name, typeName, qualified_name, and guid
    # the guid must be a negative number and unique in your batch
    # being uploaded.
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demoinputclassification01",
        guid=-100
    )
    input02 = AtlasEntity(
        name="input02",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demoinputclassification02",
        guid=-101
    )

    results = client.upload_entities(
        batch=[input01, input02]
    )

    # Get the Guids for us to work with
    guids = [v for v in results["guidAssignments"].values()]

    # Classify one entity with multiple classifications
    print(f"Adding multiple classifications to guid: {guids[0]}")
    one_entity_multi_class = client.classify_entity(
        guid=guids[0], 
        classifications=[
            AtlasClassification("MICROSOFT.PERSONAL.DATE_OF_BIRTH"),
            AtlasClassification("MICROSOFT.PERSONAL.NAME")
            ],
        force_update=True
    )
    print(json.dumps(one_entity_multi_class, indent=2))

    # Classify Multiple Entities with one classification
    try:
        multi_entity_single_class = client.classify_bulk_entities(
            entityGuids=guids,
            classification=AtlasClassification("MICROSOFT.PERSONAL.IPADDRESS")
        )
        print(json.dumps(multi_entity_single_class, indent=2))
    except AtlasException as e:
        print("One or more entities had the existing classification, so skipping it.")
        print(e)
    
