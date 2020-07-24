import os

from pyapacheatlas.core import AtlasClient
from pyapacheatlas.auth import ServicePrincipalAuthentication
import pyapacheatlas as pyaa

from dotenv import load_env

if __name__ == "__main__":
    load_env()

    oauth = ServicePrincipalAuthentication(
        tenant_id = os.environ.get("TENANT_ID"),
        client_id = os.environ.get("CLIENT_ID"),
        client_secret = os.environ.get("CLIENT_SECRET")
    )
    atlas_client = AtlasClient(
        endpoint_url =  os.environ.get("ENDPOINT_URL"),
        authentication = oauth
    )

    
    
