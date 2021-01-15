import os
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasAttributeDef, AtlasEntity, PurviewClient
from pyapacheatlas.core.typedef import EntityTypeDef


if __name__ == "__main__":
    """
    This sample provides shows how to create custom type definitions and
    how to creates entities using the custom type.
    """
    
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    edef = EntityTypeDef(
        name="pyapacheatlas_custom_type",
        attributeDefs=[
            AtlasAttributeDef("column1", typeName="string").to_json(),
            AtlasAttributeDef("column2", typeName="int").to_json(),
            AtlasAttributeDef("column3", typeName="array<string>").to_json(),
        ],
        superTypes=["DataSet"]
    )

    results = client.upload_typedefs(
        entityDefs=[edef],
        force_update=True
    )

    actual_entity = AtlasEntity(
        name="a_sample_entity_of_pyapacheatlas_custom_type",
        qualified_name="pyapacheatlas://sample_pyapacheatlas_custom_type",
        typeName="pyapacheatlas_custom_type",
        attributes={"column1": "abc", "column2": 123, "column3": ["a", "b"]},
        guid=-100
    )

    upload_results = client.upload_entities(actual_entity)

    print(json.dumps(upload_results, indent=2))
