import json
import os
import time

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.typedef import EntityTypeDef

import pytest

oauth = ServicePrincipalAuthentication(
    tenant_id=os.environ.get("TENANT_ID", ""),
    client_id=os.environ.get("CLIENT_ID", ""),
    client_secret=os.environ.get("CLIENT_SECRET", "")
)
client = PurviewClient(
    account_name = os.environ.get("PURVIEW_NAME", ""),
    authentication=oauth
)


def test_partial_update_by_guid():
    original_desc = "This is my desc"
    changed_desc = "This is an updated description"
    ae = AtlasEntity("partial01","DataSet", "tests://partial01", guid="-1",
    attributes={"description": original_desc}
    )
    
    assignments = client.upload_entities([ae])["guidAssignments"]
    try:
        live_table = client.get_entity(guid=assignments["-1"])["entities"][0]
        
        # Should have three attributes because two are from the table having the
        # relationship defined as an array of columns and the third is from
        # the column having the table relationshipAttribute defined on them.
        assert(live_table["attributes"]["description"] == original_desc)
        client.partial_update_entity(
            guid=assignments["-1"],
            attributes={"description":changed_desc}
        )
        
        # Check that we have one more relationship
        # There are caching issues here :-(
        time.sleep(10)
        live_table_post_update = client.get_entity(guid=assignments["-1"])["entities"][0]
        assert(live_table_post_update["attributes"]["description"] == changed_desc)

    finally:
        # Need to delete all columns BEFORE you delete the table
        _ = client.delete_entity(assignments["-1"])

def test_partial_update_raises_valueerror_if_not_exists():
    with pytest.raises(ValueError) as e_info:
        client.partial_update_entity(
            qualifiedName="fjdkagdjkalf", typeName="DataSet",
            attributes={"description":"gdioagpdai"}
        )
