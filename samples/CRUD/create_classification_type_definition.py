import os
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasAttributeDef, AtlasEntity, PurviewClient
from pyapacheatlas.core.typedef import ClassificationTypeDef, EntityTypeDef, TypeCategory


if __name__ == "__main__":
    """
    This sample provides shows how to create custom classifications
    for how to apply classifications to an entity see 
    `create_entity_and_classification`.
    """
    
    cred = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    # Alternatively
    from azure.identity import AzureCliCredential
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=cred
    )

    # Create a custom classification that applies to all assets
    cdef = ClassificationTypeDef(
        name="pyapacheatlas_custom_classification",
        entityTypes=["DataSet"]
    )

    # Do the upload
    results = client.upload_typedefs(
        classificationDefs=[cdef],
        force_update=True
    )

    print("Results of classification type definition:")
    print(json.dumps(results, indent=2))

    # To remove, delete the type created
    client.delete_type("pyapacheatlas_custom_classification")