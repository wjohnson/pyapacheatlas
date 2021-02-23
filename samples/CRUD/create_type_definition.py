import os
import json

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasAttributeDef, AtlasEntity, PurviewClient
from pyapacheatlas.core.typedef import EntityTypeDef, TypeCategory


if __name__ == "__main__":
    """
    This sample provides shows how to create custom type definitions and
    how to creates entities using a custom type.
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

    # Create an entity type definition with three columns (column1, 2, 3)
    # with column1 required.
    edef = EntityTypeDef(
        name="pyapacheatlas_create_type_def_sample",
        attributeDefs=[
            AtlasAttributeDef("column1", typeName="string", isOptional=False),
            AtlasAttributeDef("column2", typeName="int"),
            AtlasAttributeDef("column3", typeName="array<string>", cardinality="SET"),
        ],
        superTypes=["DataSet"]
    )

    # Do the upload
    results = client.upload_typedefs(
        entityDefs=[edef],
        force_update=True
    )

    # Just for demonstration purposes, get the entity type def.
    get_results = client.get_typedef(TypeCategory.ENTITY, name="pyapacheatlas_create_type_def_sample")
    print("# Results from getting created type def:")
    print(json.dumps(get_results,indent=2))

    # Creating an instance of this custom type
    actual_entity = AtlasEntity(
        name="instance_of_pyapacheatlas_create_type_def_sample",
        qualified_name="pyapacheatlas://instance_of_pyapacheatlas_create_type_def_sample",
        typeName="pyapacheatlas_create_type_def_sample",
        attributes={"column1": "abc", "column2": 123, "column3": ["a", "b"]},
        guid=-100
    )

    upload_results = client.upload_entities(actual_entity)

    print("# Results of entity upload:")
    print(json.dumps(upload_results, indent=2))

    # To remove, delete the entity created and then the entity type.
    # client.delete_entity(guid=["..."])
    # delete_results = client.delete_type("pyapacheatlas_create_type_def_sample")
    # print(json.dumps(delete_results, indent=2))
