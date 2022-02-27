import json
import os
import time

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient
from pyapacheatlas.core import AtlasEntity
from pyapacheatlas.core.typedef import EntityTypeDef

oauth = ServicePrincipalAuthentication(
    tenant_id=os.environ.get("TENANT_ID", ""),
    client_id=os.environ.get("CLIENT_ID", ""),
    client_secret=os.environ.get("CLIENT_SECRET", "")
)
client = PurviewClient(
    account_name = os.environ.get("PURVIEW_NAME", ""),
    authentication=oauth
)

def test_set_relationship_different_ways():

    ae = AtlasEntity("rel01","hive_table", "tests://rel01", guid=-1)
    c1 = AtlasEntity("rel01#01", "hive_column", "tests://rel01#01", guid=-2, attributes={"type":"str"})
    c2 = AtlasEntity("rel01#02", "hive_column", "tests://rel01#02", guid=-3, attributes={"type":"str"})
    c3 = AtlasEntity("rel01#03", "hive_column", "tests://rel01#03", guid=-4, attributes={"type":"str"})
    c4 = AtlasEntity("rel01#04", "hive_column", "tests://rel01#04", guid=-5, attributes={"type":"str"})

    # Add c1 as the only relationship
    ae.addRelationship(columns=[c1.to_json(minimum=True), c2.to_json(minimum=True)])

    c3.addRelationship(table = ae)

    assignments = client.upload_entities([ae, c1, c2, c3, c4])["guidAssignments"]
    try:
        live_table = client.get_entity(guid=assignments["-1"])["entities"][0]
        
        # Should have three attributes because two are from the table having the
        # relationship defined as an array of columns and the third is from
        # the column having the table relationshipAttribute defined on them.
        assert(len(live_table["relationshipAttributes"]["columns"]) == 3)

        # relationship = {
        #             "typeName": "hive_table_columns",
        #             "attributes": {},
        #             "guid": -100,
        #             # Ends are either guid or guid + typeName 
        #             # (in case there are ambiguities?)
        #             "end1": {
        #                 "guid": assignments["-1"]
        #             },
        #             "end2": {
        #                 "guid": assignments["-5"]
        #             }
        #         }

        # relation_upload = client.upload_relationship(relationship)
        # Check that we have one more relationship
        # There are caching issues here :-(
        # time.sleep(10)
        # live_table_post_relationship = client.get_entity(guid=assignments["-1"])["entities"][0]
        # assert(len(live_table["relationshipAttributes"]["columns"]) == 4)

    finally:
        # Need to delete all columns BEFORE you delete the table
        for local_id in [str(s) for s in range(-5,0)]:
            guid = assignments[local_id]
            _ = client.delete_entity(guid)
