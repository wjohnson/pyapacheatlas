import json
import os
# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity

if __name__ == "__main__":
    """
    This sample demonstrates creating, updating, and deleting custom attributes
    in Azure Purview but this could also be applied to Apache Atlas.

    Note that at time of publishing, custom attributes are not visible in the
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

    # Create an Entity With Custom Attributes
    entity = AtlasEntity(
        name="mycustomtable",
        typeName="azure_sql_table",
        qualified_name="mssql://myserver/mydb/myschema/mycustomtable",
        guid="-1"
    )
    entity.addCustomAttribute(foo="bar", buz="qux")
    resp = client.upload_entities([entity])
    guid = resp["guidAssignments"]["-1"]

    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to modifying the custom attributes")

    # There is no real "append" in Atlas / Purview for Custom Attributes
    # instead, you need to "add" all of your existing attributes and add
    # any additional custom attributes.
    entity.addCustomAttribute(baz="coo")
    resp_modified = client.upload_entities([entity])
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to deleting custom attributes")

    # There is no real "delete" in Atlas / Purview for Custom Attributes
    # instead, you need to "add" all of the existing attributes you want
    # to keep and omit any you don't want to have.
    existing_entity_resp = client.get_single_entity(guid)
    existing_entity = AtlasEntity.from_json(existing_entity_resp["entity"])
    existing_entity.customAttributes.pop("foo")
    resp_deleted = client.upload_entities([existing_entity])
    print(json.dumps(resp_deleted, indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    print("Completed demonstration of adding, updating, and removing custom attributes")
