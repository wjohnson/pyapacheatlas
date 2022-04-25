import json
import os
# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity
from pyapacheatlas.core.typedef import AtlasAttributeDef, AtlasStructDef, TypeCategory

if __name__ == "__main__":
    """
    This sample demonstrates creating, updating, and deleting custom labels
    in Azure Purview but this could also be applied to Apache Atlas.

    Note that at time of publishing, custom labels are not visible in the
    Purview UI.
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

    # Create an Entity With Business Attributes
    # Note: Rerunning this sample with the same qualified name will not work.
    # You can't update the labels via the /entity endpoint after the entity
    # has been created.
    entity = AtlasEntity(
        name="mytablewithlabels2",
        typeName="azure_sql_table",
        qualified_name="mssql://myserver/mydb/myschema/mytablewithlabels2",
        guid="-1",
        labels= ["a", "b", "c"]
    )
    resp = client.upload_entities([entity])
    guid = resp["guidAssignments"]["-1"]

    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to modifying the labels attributes")

    # Append new custom labels (without overwriting)
    resp = client.update_entity_labels(labels=['d','e'], 
        guid=guid, 
        force_update=False
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to completely overwrite the labels attributes")
    
    #  Completely overwrite custom labels with a new set of labels
    # by passing the force_update=True flag

    resp = client.update_entity_labels(
        labels=['j','k', 'l'], 
        guid=guid, 
        force_update=True
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to remove a subset of the label attributes")
    # Remove one or many Custom Labels

    resp = client.delete_entity_labels(labels=['j','k'], 
        guid=guid
    )
    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    print("Completed demonstration of adding, updating, and removing custom labels")
