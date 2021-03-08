import json
import os
import time

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.core import AtlasEntity, AtlasProcess

oauth = ServicePrincipalAuthentication(
    tenant_id=os.environ.get("TENANT_ID", ""),
    client_id=os.environ.get("CLIENT_ID", ""),
    client_secret=os.environ.get("CLIENT_SECRET", "")
)
client = PurviewClient(
    account_name=os.environ.get("PURVIEW_NAME", ""),
    authentication=oauth
)


def test_min_entity_json_no_guid_usage():

    ae = AtlasEntity("BeforeModi", "DataSet",
                     "tests://EntityRESTBeforeModification", guid=-1)

    assignments = client.upload_entities([ae])["guidAssignments"]
    assign_with_no_guid = {}
    try:
        # live_table = client.get_entity(guid=assignments["-1"])["entities"][0]
        ae_no_guid = AtlasEntity(
            "BeforeModi", "DataSet", "tests://EntityRESTBeforeModification", guid=None)

        proc1 = AtlasProcess("WillBeUpdatedWithNoGuidEntity", "Process",
                             "tests://EntityRESTBeforeModificationProc",
                             inputs=[ae_no_guid], outputs=[], guid=-2)
        assign_with_no_guid = client.upload_entities([proc1])["guidAssignments"]

        live_proc = client.get_entity(guid=assign_with_no_guid["-2"])["entities"][0]

        # Should have one input that matches the guid assignment 
        assert(len(live_proc["attributes"]["inputs"]) == 1)
        assert(live_proc["attributes"]["inputs"][0]["guid"] == assignments["-1"])

    finally:
        # Delete the entities now that the test is complete
        _ = client.delete_entity(assignments["-1"])
        if "-2" in assign_with_no_guid:
            _ = client.delete_entity(assign_with_no_guid.get("-2"))
        pass
        
