import json
import os

from azure.identity import AzureCliCredential
# PyApacheAtlas packages
from pyapacheatlas.core import PurviewClient, AtlasEntity

if __name__ == "__main__":
    """
    This sample provides an example of creating a custom lineage 'manually'
    through the rest api / pyapacheatlas classes.

    This uses the Microsoft Purview built-in relationships of Sources and
    Sinks. This is an undocumented feature and may change but it helps to
    address the many individuals who wish to represent lineage without
    a process entity in between two assets.

    This is an advanced, undocumented feature. I would encourage you to stick
    with the documented Apache Atlas style as seen in the `create_entity_and_lineage`
    sample.
    """

    # Authenticate against your Atlas server
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", "DefaultPurviewAccountName"),
        authentication=cred
    )

    # Create two entities with AtlasEntity to represent source and sink
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://sourceLineageSample01",
        guid="-100"
    )
    output01 = AtlasEntity(
        name="output01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://sinkLineageSample02",
        guid="-101"
    )

    # Add a "sinks" relationship on the input side
    # This will make the Microsoft Purview Lineage graph
    # represent `input01` as the source to the `output01`
    # entity
    input01.addRelationship(sinks=[output01])

    # Convert the individual entities into json before uploading.
    results = client.upload_entities(
        batch=[output01, input01]
    )

    print(json.dumps(results, indent=2))
