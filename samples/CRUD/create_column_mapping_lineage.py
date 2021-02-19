import json
import os
# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess
from pyapacheatlas.core.typedef import EntityTypeDef, AtlasAttributeDef
from pyapacheatlas.core.util import GuidTracker

if __name__ == "__main__":
    """
    This sample demonstrates using the columnMapping feature of Azure Purview.
    You will create a process with two inputs and one output. From there you
    will create a valid column mapping JSON object that will display column
    level lineage in the Purview UI.
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

    # We need a custom process entity type that contains the definition for
    # a columnMapping attribute.
    procType = EntityTypeDef(
        "ProcessWithColumnMapping",
        superTypes=["Process"],
        attributeDefs = [
            AtlasAttributeDef("columnMapping")
        ]
    )

    # Upload the type definition
    type_results = client.upload_typedefs(entityDefs=[procType], force_update=True)
    print(json.dumps(type_results,indent=2))

    # Set up a guid tracker to make it easier to generate negative guids
    gt = GuidTracker()

    # Now we can create the entities, we will have two inputs and one output
    colMapInput01 = AtlasEntity(
        "Input for Column Mapping",
        "hive_table",
        "pyapacheatlas://colMapInput01",
        guid=gt.get_guid()
    )
    colMapInput02 = AtlasEntity(
        "Second Input for Column Mapping",
        "hive_table",
        "pyapacheatlas://colMapInput02",
        guid=gt.get_guid()
    )
    colMapOutput01 = AtlasEntity(
        "Output for Column Mapping",
        "hive_table",
        "pyapacheatlas://colMapOutput01",
        guid=gt.get_guid()
    )
    
    # Now we can define the column mapping object that will be 'stringified'
    # and given to our process entity
    column_mapping = [
        # This object defines the column lineage between input01 and output01
        {"ColumnMapping": [
            {"Source": "In01Address", "Sink": "Out01Address"},
            {"Source": "In01Customer", "Sink": "Out01Customer"}],
            "DatasetMapping": {
            "Source": colMapInput01.qualifiedName, "Sink": colMapOutput01.qualifiedName}
         },
        # This object defines the column lineage between input02 and output01
        {"ColumnMapping": [
            {"Source": " In02AnnualSales", "Sink": "Out01AnnualSales"},
            {"Source": " In02PostalCode", "Sink": "Out01Address"}],
            "DatasetMapping": {"Source": colMapInput02.qualifiedName, "Sink": colMapOutput01.qualifiedName}
         },
         # This object demonstrates a "special case" of defining fields for one
         # table. The Source is an asterisk for both column mapping and dataset
         # mapping. This is most commonly used to represent "This Sink field is
         # made up of many inputs across all the tables involved in lineage".
         {"ColumnMapping": [
            {"Source": "*", "Sink": "Out01UniqueField3"},
            {"Source": "*", "Sink": "Out01UniqueField4"}],
            "DatasetMapping": {"Source":"*","Sink": colMapOutput01.qualifiedName}
         },
         # This is another example of the above special case for an input object
         {"ColumnMapping": [
            {"Source": "*", "Sink": "In01UniqueField"},
            {"Source": "*", "Sink": "In01UniqueField2"}],
            "DatasetMapping": {"Source": "*", "Sink": colMapInput01.qualifiedName}
         }
    ]

    # Create the process with the stringified column mapping json.
    process = AtlasProcess(
        name="test process",
        typeName="ProcessWithColumnMapping",
        qualified_name="pyapacheatlas://colMapOutputProcessDemo",
        inputs=[colMapInput01, colMapInput02],
        outputs=[colMapOutput01],
        guid=gt.get_guid(),
        attributes={"columnMapping": json.dumps(column_mapping)}
    )

    results = client.upload_entities(
        [process, colMapInput01, colMapInput02, colMapOutput01]
    )

    print(json.dumps(results, indent=2))
    sink_guid = results["guidAssignments"][str(colMapOutput01.guid)]
    print(f"Search for \"{colMapOutput01.name}\" or use the guid {sink_guid} to look up the sink table.")
