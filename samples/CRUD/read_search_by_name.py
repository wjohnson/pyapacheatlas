import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

if __name__ == "__main__":
    """
    This sample provides an example of searching for an existing entity
    through the rest api / pyapacheatlas classes.

    NOTE: This example is specific to Azure Purview's Advanced Search.

    The response is a Python generator that allows you to page through the
    search results. For each page in the search results, you have a list
    of search entities that can be iterated over.
    """

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    # Assuming you have an entity with the word demo in the name or description
    search = client.discovery.search_entities("demo")

    # Alternative search methods include...
    # Searching across a given attribute:
    # Search only the name (or qualifiedName) field and it begins with demo
    # Must include a wildcard character (*) at the end, does not support
    # wildcard at the beginning or middle.

    # search = client.discovery.search_entities("name:demo*")
    # search = client.discovery.search_entities("qualifiedName:demo*")

    # Searching within a given type and include subtypes...
    # Provide a search filter that specifies the typeName and whether
    # you want to include sub types of that type or not.

    # filter_setup = {"typeName": "DataSet", "includeSubTypes": True}
    # search = client.discovery.search_entities("*", search_filter=filter_setup)

    # The response is a Python generator that allows you to page through the
    # search results without having to worry about paging or offsets.
    for entity in search:
        # Important properties returned include...
        # id (the guid of the entity), name, qualifedName, @search.score,
        # and @search.highlights
        print(json.dumps(entity, indent=2))
