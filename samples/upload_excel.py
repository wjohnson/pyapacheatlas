import json
import os

from pyapacheatlas.core import AtlasClient
from pyapacheatlas.auth import ServicePrincipalAuthentication
import pyapacheatlas as pyaa

if __name__ == "__main__":

    oauth = ServicePrincipalAuthentication(
        tenant_id = os.environ.get("TENANT_ID"),
        client_id = os.environ.get("CLIENT_ID"),
        client_secret = os.environ.get("CLIENT_SECRET")
    )
    atlas_client = AtlasClient(
        endpoint_url =  os.environ.get("ENDPOINT_URL"),
        authentication = oauth
    )

    excel_output = pyaa.from_excel("./atlas_excel_template.xlsx")

    # Investigate batch
    print(len(excel_output))
    print(excel_output[0:5])

    # Convert to json to prepare for upload
    batch = [e.to_json() for e in excel_output]

    results = atlas_client.upload_entities(batch)

    print(results)
