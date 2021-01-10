import json
import os

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

if __name__ == "__main__":
    """
    This sample provides an example of updating a custom lineage and an existing
    entity 'manually' through the rest api / pyapacheatlas classes.

    Lineage can be updated for an entity by changing the inputs or outputs
    attributes of a Process entity.

    An existing entity can be updated by uploading a partial update. Only
    attributes that are referenced will be updated, all others stay the same.
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

    # Assuming you want to update all of the inputs, all of the outputs, or
    # all of both, we can create an AtlasProcess object with the minimum
    # requirements of name, typeName, and qualifedName.

    # Start with null/None inputs and outputs and we will fill them in.
    # existing_process = AtlasProcess(
    #     name="sample_process_xyz",
    #     typeName="Process",
    #     qualified_name="pyapacheatlas://democustomprocess",
    #     inputs=None, # Set to None so no update will occur
    #     outputs=None, # We will update this with set_outputs below
    #     guid=-101
    # )

    # new_output = AtlasEntity(
    #     name="output03",
    #     typeName="DataSet",
    #     qualified_name="pyapacheatlas://demooutput03",
    #     guid=-102
    # )

    # # Completely overwrite the outputs
    # existing_process.set_outputs(
    #     [ new_output.to_json(minimum=True) ]
    # )

    # # Convert the individual entities into json before uploading.
    # results = client.upload_entities(
    #     batch = [new_output.to_json(), existing_process.to_json()]
    # )

    # print(json.dumps(results, indent=2))

    print("Starting Append Scenario...")
    # A second scenario would have us appending to an existing process
    # To do that, we need to query for the existing entity
    dummy_existing_process = AtlasProcess(
        name="sample_process_xyz",
        typeName="Process",
        qualified_name="pyapacheatlas://democustomprocess",
        inputs=None,  # Set to None so no update will occur
        outputs=None,  # We will update this with set_outputs below
        guid=-104
    )

    real_existing_process = client.get_entity(
        typeName="Process",
        qualifiedName="pyapacheatlas://democustomprocess"
    )["entities"][0]
    print("Working with process guid: {}".format(
        real_existing_process["guid"]))

    # Get the list of existing outputs from the attributes.
    existing_outputs = real_existing_process["attributes"]["outputs"]

    # Create one more output to be added.
    one_more_output = AtlasEntity(
        name="output_added_later",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demooutput04",
        guid=-103
    )

    # Add the existing and new output to the dummy process
    dummy_existing_process.set_outputs(
        existing_outputs + [one_more_output.to_json(minimum=True)]
    )

    complex_results = client.upload_entities(
        batch=[dummy_existing_process.to_json(), one_more_output.to_json()]
    )

    print(json.dumps(complex_results, indent=2))
