import json
import os

from pyapacheatlas.core import AtlasClient
from pyapacheatlas.auth import OAuthMSFT
import pyapacheatlas as pyaa

from dotenv import load_env

if __name__ == "__main__":
    load_env()

    oauth = OAuthMSFT(
        tenant_id = os.environ.get("TENANT_ID"),
        client_id = os.environ.get("CLIENT_ID"),
        client_secret = os.environ.get("CLIENT_SECRET")
    )
    atlas_client = AtlasClient(
        endpoint_url =  os.environ.get("ENDPOINT_URL"),
        authentication = oauth
    )

    batch = pyaa.from_excel("./atlas_excel_template.xlsx")

    # Investigate batch
    print(len(batch))

    print(json.dumps(batch[0:5], indent=2))

    results = atlas_client.upload_entities(batch)

    print(results)
