import time
import os
import sys
import array

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

filename = sys.argv[1]

oauth = ServicePrincipalAuthentication(
    tenant_id = os.environ.get('AZURE_TENANT_ID', ''),
    client_id = os.environ.get('AZURE_CLIENT_ID', ''),
    client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')
    )
client = PurviewClient(
    account_name = os.environ.get('PURVIEW_CATALOG_NAME', ''),
    authentication = oauth
    )

infile=open(filename)
guids = []
for line in infile:
    guids.append(line.strip())
client.delete_entity(guids)
infile.close()
os.remove(filename)