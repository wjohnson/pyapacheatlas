import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import AtlasClient, AtlasEntity, AtlasProcess

if __name__ == "__main__":
    """
    This sample provides an example of creating a custom lineage 'manually'
    through the rest api / pyapacheatlas classes.

    Custom Lineage requires at least three entities. One 'Process' entity
    and at least two 'DataSet' entities. The process entity takes in the
    two dataset entities ('minified' to be just the guid, qualifiedname,
    and type) as inputs and outputs.

    Then the entities are uploaded to your Data Catalog and resulting json
    is printed.
    """

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = AtlasClient(
        endpoint_url=os.environ.get("ENDPOINT_URL", ""),
        authentication=oauth
    )

    # Create two entities with AtlasEntity
    # You must provide a name, typeName, qualified_name, and guid
    # the guid must be a negative number and unique in your batch
    # being uploaded.
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demoinput01",
        guid=-100
    )
    output01 = AtlasEntity(
        name="output01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demooutput01",
        guid=-101
    )

    # The Atlas Process is the lineage component that links the two
    # entities together. The inputs and outputs need to be the "header"
    # version of the atlas entities, so specify minimum = True to
    # return just guid, qualifiedName, and typeName.
    process = AtlasProcess(
        name="sample process",
        typeName="Process",
        qualified_name="pyapacheatlas://democustomprocess",
        inputs=[input01.to_json(minimum=True)],
        outputs=[output01.to_json(minimum=True)],
        guid=-102
    )

    # Convert the individual entities into json before uploading.
    results = client.upload_entities(
        batch = [output01.to_json(), input01.to_json(), process.to_json()]
    )
    
    print(json.dumps(results, indent=2))