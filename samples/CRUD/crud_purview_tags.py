import json
import os
# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity
from pyapacheatlas.core.typedef import AtlasAttributeDef, AtlasStructDef, TypeCategory

if __name__ == "__main__":
    """
    This sample demonstrates creating, updating, and deleting custom tags (a.k.a. label)
    
    Note that the `_tags` methods are facades over the `_labels` methods since
    Microsoft Purview renamed labels to tags in the Microsoft Purview UI.
    """
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("TENANT_ID", "YourDefaultTenantId"),
        client_id=os.environ.get("CLIENT_ID", "YourDefaultClientId"),
        client_secret=os.environ.get("CLIENT_SECRET", "YourDefaultClientSecretValue")
    )
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", "DefaultPurviewAccountName"),
        authentication=oauth
    )

    # Create an Entity With Labels/Tags
    # Note: Rerunning this sample with the same qualified name will not work.
    # You can't update the labels via the /entity endpoint after the entity
    # has been created.
    entity = AtlasEntity(
        name="MyTableWithTags",
        typeName="azure_sql_table",
        qualified_name="mssql://myserver/mydb/myschema/MyTableWithTags",
        guid="-1",
        labels= ["a", "b", "c"]
    )
    resp = client.upload_entities([entity])
    guid = resp["guidAssignments"]["-1"]

    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to modifying the labels attributes")

    # Append new custom labels (without overwriting)
    resp = client.update_entity_tags(labels=['d','e'], 
        guid=guid, 
        force_update=False
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to completely overwrite the labels attributes")
    
    #  Completely overwrite custom labels with a new set of labels
    # by passing the force_update=True flag

    resp = client.update_entity_tags(
        labels=['j','k', 'l'], 
        guid=guid, 
        force_update=True
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to remove a subset of the label attributes")
    # Remove one or many Custom Labels

    resp = client.delete_entity_tags(labels=['j','k'], 
        guid=guid
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    print("Completed demonstration of adding, updating, and removing custom labels")
