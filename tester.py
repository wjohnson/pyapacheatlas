tenant_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"
client_id = "50744756-c0ad-4d5b-b1d6-33bb766c4114"
client_secret = "31z_KD90hZV-JJ8pdNC.O.702pOPD3G_cc"
data_catalog_name = "contosobabylon"

atlas_endpoint = "https://" + data_catalog_name + ".catalog.azure.com/api/atlas/v2"

import json
import os

from pyapacheatlas.auth import OAuthMSFT
from pyapacheatlas.core import AtlasClient
from pyapacheatlas.core import TypeCategory
from pyapacheatlas.readers.excel import from_excel, ExcelConfiguration
from pyapacheatlas.scaffolding import column_lineage_scaffold

import pyapacheatlas as pyaa


if __name__ == "__main__":

    oauth = OAuthMSFT(
        tenant_id = tenant_id,
        client_id = client_id,
        client_secret = client_secret
    )
    atlas_client = AtlasClient(
        endpoint_url =  atlas_endpoint,
        authentication = oauth
    )

    # entity = atlas_client.get_entity(guid=["95f5da92-545b-44ac-8393-427f706cc7bb", 
    # "d1757da8-351f-405f-ac5f-b06e34fe6d77", "79e5659a-70c9-4ac9-bced-d28ac86a60cd", 
    # "5990c3c8-bfba-4b19-b0a6-9790db431665", "f1284b8d-896a-4c9b-9bb9-e300d5277a69"])
    # print(json.dumps(entity, indent=2))


    # scaffolding = column_lineage_scaffold("demo", useColumnMapping=True)

    # print(json.dumps(scaffolding, indent=2))

    demo_entity = {
      "typeName": "hive_table",
      "attributes": {
        "owner": "admin",
        "qualifiedName": "willjohnson_test_upload_hivetable",
        "columns": [],
        "description": "This is a test table!",
        "tableType": "MANAGED_TABLE",
        "name": "testing_a_hive_upload",
      },
      "guid": "-1000",
      "status": "ACTIVE",
      "relationshipAttributes": {}
    }

    results = atlas_client.upload_entities(demo_entity)

    print(json.dumps(results, indent=2))



    # upload_results = atlas_client.upload_typedefs(scaffolding)
    # print(upload_results)
    # print("\n"*3)

    # config = ExcelConfiguration(
    #     entity_sheet = "Sheet1",
    # )

    # results = pyaa.from_excel('./test.xlsx', config)

    # print(json.dumps([e.to_json() for e in results], indent=2))


    # results = atlas_client.get_typedef(type_category=TypeCategory.ENTITY, name="mssql_table")
    # print(results)


