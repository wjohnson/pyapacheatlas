import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient

if __name__ == "__main__":
    """
    This sample provides an example of creating a single term.

    In this example, we create a term and have a framework for adding
    a parent term to it as well.

    Currently, PyApacheAtlas only supports Azure Purview.
    """

    # Authenticate against your Purview service
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name = os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    # This is the bare minimum we need to upload
    # a custom term with no parent information and have it set to Draft
    results = client.upload_term("my custom term")
    # You could also change the status to Active
    results = client.upload_term("my second term", status="Active")
    # You also might add in a term's description
    results = client.upload_term("my third term", long_description="This is my term's description.")

    # If you plan on adding a parent hierarchy, it's important to
    # get the guid of the glossary and the parent term in advance
    # especially if you are planning on adding many terms.
    glossary = client.get_glossary()
    glossary_guid = glossary["guid"]
    parent_term_guid = None
    parent_formal_name = "my custom term"

    # If you've defined a parent_formal_name, you'll need to get the guid
    # The method will query it for you if it's not provided but if you
    # plan on adding multiple terms, this is more efficient from an API call count
    if parent_formal_name:
        for term in glossary["terms"]:
            if term["displayText"] == parent_formal_name:
                parent_term_guid = term["termGuid"]
        if parent_term_guid is None:
            raise ValueError(f"The term {parent_formal_name} isn't found and can't be added as a parent")

    # Now that the parent formal name and guid are found,
    # we can upload to Purview.
    hierarchy_results = client.upload_term("my child term",
        glossary_guid=glossary_guid,
        parent_formal_name=parent_formal_name, 
        parent_term_guid=parent_term_guid)

    print(hierarchy_results)
