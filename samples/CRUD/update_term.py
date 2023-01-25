import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient
from pyapacheatlas.core.glossary.term import PurviewGlossaryTerm

if __name__ == "__main__":
    """
     This sample provides an example of creating and then updating a glossary term.
    """
    # Authenticate against your Atlas server
    cred = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", ""),
        client_id=os.environ.get("CLIENT_ID", ""),
        client_secret=os.environ.get("CLIENT_SECRET", "")
    )
    # Alternatively, use Azure CLI Credential
    # from azure.identity import AzureCliCredential
    # cred = AzureCliCredential()
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=cred
    )

    # Get the glossary guid to know where to upload the term
    glossary = client.glossary.get_glossary(name="Glossary")

    # Create the initial term
    term = PurviewGlossaryTerm(
        name = "foo",
        qualifiedName="foo@Glossary",
        glossaryGuid = glossary["guid"],
        longDescription = "This is an initial short description"
    )
    create_response = client.glossary.upload_term(term)

    # Extract the guid from the created term for use in update
    termGuid = create_response["guid"]

    # Make a change
    term.longDescription = "This is a second much longer description"

    # Force an update
    update_response = client.glossary.upload_term(term, force_update=True, termGuid=termGuid)
    print(json.dumps(update_response, indent=2))
