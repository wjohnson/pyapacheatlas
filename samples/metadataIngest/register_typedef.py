import os
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

print(os.environ.get('AZURE_TENANT_ID', ''))

oauth = ServicePrincipalAuthentication(
    tenant_id = os.environ.get('AZURE_TENANT_ID', ''),
    client_id = os.environ.get('AZURE_CLIENT_ID', ''),
    client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')
    )
client = PurviewClient(
    account_name = os.environ.get('PURVIEW_CATALOG_NAME', ''),
    authentication = oauth
    )
client.upload_typedefs(json.load(open('./pyapacheatlas_mysql_typedefs_v2.json','r')), force_update=True)