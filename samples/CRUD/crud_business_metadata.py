import json
import os
# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity
from pyapacheatlas.core.typedef import AtlasAttributeDef, AtlasStructDef, TypeCategory

if __name__ == "__main__":
    """
    This sample demonstrates creating, updating, and deleting business metadata
    attributes in Azure Purview but this could also be applied to Apache Atlas.

    Note that at time of publishing, business attributes are not visible in the
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

    # Create a Business Metadata Type Definition
    # I need to include two required options
    ## maxStrLength 
    ## a jsonified array of applicableEntityTypes which defines which types can this apply to
    
    bizdef = AtlasStructDef(
        name="operations",
        category=TypeCategory.BUSINESSMETADATA,
        attributeDefs=[
            AtlasAttributeDef(name="expenseCode",options={"maxStrLength": "500","applicableEntityTypes":"[\"DataSet\"]"}),
            AtlasAttributeDef(name="criticality",options={"maxStrLength": "500", "applicableEntityTypes":"[\"DataSet\"]"})
        ]
    )
    resp = client.upload_typedefs(businessMetadataDefs=[bizdef], force_update=True)

    # Create an Entity With Business Attributes
    # Note: Rerunning this sample with the same qualified name will not work.
    # You can't update the business attributes via the /entity endpoint after
    # the entity has been created.
    entity = AtlasEntity(
        name="mybiztable",
        typeName="azure_sql_table",
        qualified_name="mssql://myserver/mydb/myschema/mybiztable",
        guid="-1"
    )
    entity.addBusinessAttribute(operations={"expenseCode":"123", "criticality":"low"})
    resp = client.upload_entities([entity])
    guid = resp["guidAssignments"]["-1"]

    print(json.dumps(resp,indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to modifying the business attributes")

    # You add or update a business attribute using the update_businessMetadata
    # method. Specify force_update=True to overwrite attributes you specify
    # and remove any attribute you have not specified.
    resp_update = client.update_businessMetadata(
        guid=guid,
        businessMetadata={
        "operations":{"expenseCode":"1011"}
        }
    )
    print(json.dumps(client.get_single_entity(guid),indent=2))

    _ = input(">>>Press enter to continue to deleting business attributes")

    # You delete a specific business metadata attribute on an entity by using
    # the delete_businessMetadata method. You should specify the business
    # metadata typedef name and then the attribute you want to delete.
    resp_deleted = client.delete_businessMetadata(
        guid=guid,
        businessMetadata={"operations":{"criticality":""}}
        )
    print(json.dumps(resp_deleted, indent=2))
    print(json.dumps(client.get_single_entity(guid),indent=2))

    print("Completed demonstration of adding, updating, and removing business attributes")
