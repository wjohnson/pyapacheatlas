import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasClassification, AtlasEntity, AtlasProcess
from pyapacheatlas.core.util import AtlasException

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

def test_classify_entities():
    # Create an entity
    # You must provide a name, typeName, qualified_name, and guid
    # the guid must be a negative number and unique in your batch
    # being uploaded.
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="tests://classify_01",
        guid=-100
    )
    input02 = AtlasEntity(
        name="input02",
        typeName="DataSet",
        qualified_name="tests://classify_02",
        guid=-101
    )

    results = client.upload_entities(
        batch=[input01, input02]
    )

    # Get the Guids for us to work with
    guids = [v for v in results["guidAssignments"].values()]

    try:
        one_entity_multi_class = client.classify_entity(
            guid=guids[0], 
            classifications=[
                AtlasClassification("MICROSOFT.PERSONAL.DATE_OF_BIRTH"),
                AtlasClassification("MICROSOFT.PERSONAL.NAME")
                ],
            force_update=True
        )

        assert(one_entity_multi_class)

        multi_entity_single_class = client.classify_bulk_entities(
            entityGuids=guids,
            classification=AtlasClassification("MICROSOFT.PERSONAL.IPADDRESS")
        )

        assert(multi_entity_single_class)
    finally:
        for guid in guids:
            _ = client.delete_entity(guid)