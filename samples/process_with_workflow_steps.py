import json
import os

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, TypeCategory
from pyapacheatlas.core.typedef import (
    ChildEndDef,
    EntityTypeDef,
    RelationshipTypeDef,
    ParentEndDef
)

if __name__ == "__main__":
    """
    This sample shows how you might create a process that contains a set of
    steps but no intermediate data is produced / being captured. You might
    want to capture all the steps in a process and that can be accomplished
    with creating a custom relationship and a custom 'process_step' type.
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

    # Create a Process Type that will store the steps
    processWithSteps = EntityTypeDef(
        name="process_with_steps",
        superTypes=["Process"],
        options={
            # This makes the step entities appear in the schema tab
            "schemaElementsAttribute": "steps"
        },
    )

    # Create a step in a process type to house the actual types
    processSteps = EntityTypeDef(
        name="step_in_process",
        superTypes=["DataSet"]
    )

    # Create a relationship between the process and steps
    relationship = RelationshipTypeDef(
        name="process_with_steps_steps",
        relationshipCategory="COMPOSITION",
        # Use the Parent/Child standard end definitions
        # "steps" will be an attribute on the process_with_steps entities
        # it will contain a list of step_in_process and display on the schema.
        # "parent_process" will be an attribute on the step_in_process entity.
        endDef1=ParentEndDef(name="steps", typeName="process_with_steps"),
        endDef2=ChildEndDef(name="parent_process", typeName="step_in_process")
    )

    # Create the process, steps in the process, and dummy inputs and outputs
    # for the lineage visualization
    step01 = AtlasEntity(
        name="Step01: Do something",
        qualified_name="process_xyz#step01",
        typeName="step_in_process",
        guid=-1000,
        description="This is the first step in which we do something."
    )
    step02 = AtlasEntity(
        name="Step02: Modify the data",
        qualified_name="process_xyz#step02",
        typeName="step_in_process",
        guid=-1001,
        description="This is the second step in which modify things."
    )
    step03 = AtlasEntity(
        name="Step03: Finalize the data",
        qualified_name="process_xyz#step03",
        typeName="step_in_process",
        guid=-1002,
        description="This is the third step in which we finalize things."
    )

    input01 = AtlasEntity(
        name="demoinput01",
        qualified_name="demoinput01",
        guid=-5000,
        typeName="DataSet"
    )
    output01 = AtlasEntity(
        name="demooutput01",
        qualified_name="demooutput01",
        guid=-5001,
        typeName="DataSet"
    )

    parent = AtlasEntity(
        name="my_complex_workflow",
        qualified_name="process_xyz",
        typeName="process_with_steps",
        guid=-1003,
        relationshipAttributes={
            "steps": [
                step01.to_json(minimum=True),
                step02.to_json(minimum=True),
                step03.to_json(minimum=True),
            ]},
        attributes={
            "inputs": [input01.to_json(minimum=True)],
            "outputs": [output01.to_json(minimum=True)]
        }
    )

    # Create a batch of entities to be uploaded to Purview
    batch = [
        step01, step02,
        step03, parent,
        input01, output01
    ]

    # Upload the types
    typeResults = client.upload_typedefs(
        entityDefs=[processWithSteps, processSteps],
        relationshipDefs=[relationship],
        force_update=True
    )

    # Upload the entities
    results = client.upload_entities(batch)

    # Print the results of the entities upload
    print(json.dumps(results, indent=2))
    print("Successfully created types and entities!")
