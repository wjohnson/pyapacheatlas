import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.client import PurviewClient
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

def test_upload_typedef_with_mixed_classes():

    e = EntityTypeDef("pyapacheatlas_test1")
    e2 = EntityTypeDef("pyapacheatlas_test2")
    e3 = EntityTypeDef("pyapacheatlas_test3")
    
    results = client.upload_typedefs(
        entityDefs = [e, e2.to_json(), e3],
        force_update=True
    )
    assert(len(results["entityDefs"]) == 3)

    client.delete_type("pyapacheatlas_test1")
    client.delete_type("pyapacheatlas_test2")
    client.delete_type("pyapacheatlas_test3")
    
    