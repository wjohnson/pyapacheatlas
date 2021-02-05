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
    # One table will be added
    table = AtlasEntity("rel10","hive_table", "tests://rel10", guid=-1)
    # Four columns will be added
    c1 = AtlasEntity("rel10#01", "hive_column", "tests://rel10#c", guid=-2, attributes={"type":"str"})
    c2 = AtlasEntity("rel10#02", "hive_column", "tests://rel02#c", guid=-3, attributes={"type":"str"})
    c3 = AtlasEntity("rel10#03", "hive_column", "tests://rel03#c", guid=-4, attributes={"type":"str"})
    c4 = AtlasEntity("rel10#04", "hive_column", "tests://rel04#c", guid=-5, attributes={"type":"str"})

    # Add relationships to the columns from the table overwriting existing columns
    # Good if you want to overwrite existing schema or creating a brand new table
    # and Schema.
    columns_to_add = [ c1, c2, c3 ]
    # Use a list comprehension to convert them into dictionaries when adding a list
    table.addRelationship(columns=[c.to_json(minimum=True) for c in columns_to_add])

    # OR Add a table relationship to a column. This lets you essentially APPEND
    # a column to a table's schema.
    c4.addRelationship(table = table)

    # Upload all of the tables and columns that are referenced.
    assignments = client.upload_entities([table, c1, c2, c3, c4])["guidAssignments"]
        
    # Check that we have one more relationship
    print("Now we can see that there should be one more relationship attribute.")
    live_table_post_relationship = client.get_entity(guid=assignments["-1"])["entities"][0]
    print(json.dumps(live_table_post_relationship["relationshipAttributes"], indent=2))

    # Alternatively, you can upload a relationship directly, though this is
    # only useful for one at a time uploads and not the most efficient way.
    # relationship = {
    #     # When creating manually, you have to "know" the typeName
    #     # and the types of each end.
    #     "typeName": "hive_table_columns",
    #     "attributes": {},
    #     "guid": -100,
    #     # Ends are either guid or guid + typeName 
    #     # (in case there are ambiguities?)
    #     # End1 is the hive_table
    #     "end1": {
    #         "guid": "abc-123-def-456"
    #     },
    #     # End2 is the hive_column
    #     "end2": {
    #         "guid": "ghi-789-jkl-101"
    #     }
    # }
    # relation_upload = client.upload_relationship(relationship)