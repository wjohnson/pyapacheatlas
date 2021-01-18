import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

if __name__ == "__main__":
    """
    This sample provides an example of creating relationships in multiple ways
    through the rest api / pyapacheatlas classes.

    In this example, we look at adding columns to a hive table. The hive_table
    has a `columns` relationship attribute. It takes an array of hive_column
    entities. The hive_column has a `table` relationship attribute. It takes
    a single hive_table entity.

    Adding via the hive_table works best during initial entity creation.
    * If you re-upload the entity with different columns or less columns
    it will remove the relationship on the original columns (that aren't)
    mentioned.

    Adding via the hive_column works during and after the hive_table creation.
    * In the example below, we create a batch of entities that includes a
    partial set of columns defined on the hive_table and an additional
    hive_column with the table relationship attribute set.

    Lastly, you can always upload an individual relationship with hive_table
    and hive_columns defined on each end. However, this is the slowest path
    as it can only take one upload at a time whereas entity uploads can be
    many entities at a time.
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

    # Creating the entities that will be used in uploads.
    table = AtlasEntity("rel01","hive_table", "tests://rel01", guid=-1)
    c1 = AtlasEntity("rel01#01", "hive_column", "tests://rel01#c", guid=-2, attributes={"type":"str"})
    c2 = AtlasEntity("rel01#02", "hive_column", "tests://rel02#c", guid=-3, attributes={"type":"str"})
    c3 = AtlasEntity("rel01#03", "hive_column", "tests://rel03#c", guid=-4, attributes={"type":"str"})
    c4 = AtlasEntity("rel01#04", "hive_column", "tests://rel04#c", guid=-5, attributes={"type":"str"})

    # Add c1 as the only relationship to the table
    table.addRelationship(columns=[c1.to_json(minimum=True)])

    c2.relationshipAttributes.update({"table": table.to_json(minimum=True) })
    c3.addRelationship(table = table)

    assignments = client.upload_entities([table, c1, c2, c3, c4])["guidAssignments"]

    try:
        live_table = client.get_entity(guid=assignments["-1"])["entities"][0]
        
        # Should have two attributes because one is from the table having the
        # relationship defined as an array of columns and the second two from
        # the column's having the table relationshipAttribute defined on them.
        print("Here's what the upload looks like!")
        print(json.dumps(live_table["relationshipAttributes"], indent=2))
        print("Now we are creating a relationship.")

        relationship = {
                    # When creating manually, you have to "know" the typeName
                    # and the types of each end.
                    "typeName": "hive_table_columns",
                    "attributes": {},
                    "guid": -100,
                    # Ends are either guid or guid + typeName 
                    # (in case there are ambiguities?)
                    # End1 is the hive_table
                    "end1": {
                        "guid": assignments["-1"]
                    },
                    # End2 is the hive_column
                    "end2": {
                        "guid": assignments["-5"]
                    }
                }

        relation_upload = client.upload_relationship(relationship)
        
        # Check that we have one more relationship
        print("Now we can see that there should be one more relationship attribute.")
        live_table_post_relationship = client.get_entity(guid=assignments["-1"])["entities"][0]
        print(json.dumps(live_table_post_relationship["relationshipAttributes"], indent=2))

    finally:
        # Need to delete all columns BEFORE you delete the table
        for local_id in [str(s) for s in range(-5,0)]:
            guid = assignments[local_id]
            _ = client.delete_entity(guid)