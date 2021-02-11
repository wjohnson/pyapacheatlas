import json
import os

from pyapacheatlas.auth import BasicAuthentication, ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient, AtlasEntity, AtlasProcess, PurviewClient
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader

ae_in = AtlasEntity("test_in", "hive_table", "test://lineage_hive_in", -101)
ae_out = AtlasEntity("test_out", "hive_table", "test://lineage_hive_out", -102)
proc = AtlasProcess("test_proc", "Process", "test://lineage_hive_out", guid=-103,
                    inputs=[ae_in], outputs=[ae_out]
                    )
LINEAGE_BATCH = [ae_in, ae_out, proc]

auth = BasicAuthentication(username="admin", password="admin")
client = AtlasClient(endpoint_url="http://localhost:21000/api/atlas/v2",
                     authentication=auth)

oauth = ServicePrincipalAuthentication(
    tenant_id=os.environ.get("TENANT_ID", ""),
    client_id=os.environ.get("CLIENT_ID", ""),
    client_secret=os.environ.get("CLIENT_SECRET", "")
)
purview_client = PurviewClient(
    account_name=os.environ.get("PURVIEW_NAME", ""),
    authentication=oauth
)


def test_lineage_atlas():

    results = client.upload_entities(batch=LINEAGE_BATCH)
    assignments = results["guidAssignments"]

    lineage = client.get_entity_lineage(assignments["-103"])

    try:
        assert(len(lineage["guidEntityMap"]) == 3)
    finally:
        client.delete_entity(guid=[v for v in assignments.values()])


def test_lineage_next_purview():
    results = purview_client.upload_entities(batch=LINEAGE_BATCH)
    assignments = results["guidAssignments"]

    lineage = purview_client.get_entity_next_lineage(
        guid=assignments["-102"],
        direction="INPUT",
        offset=0,
        limit=1
    )

    try:
        assert(len(lineage["guidEntityMap"]) == 2)
    finally:
        purview_client.delete_entity(guid=[v for v in assignments.values()])
