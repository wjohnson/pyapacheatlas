import json
import os

from azure.identity import AzureCliCredential
from pyapacheatlas.core import AtlasEntity, AtlasProcess, PurviewClient
from pyapacheatlas.core.entity import AtlasClassification
from pyapacheatlas.core.glossary.term import AtlasGlossaryTerm
from pyapacheatlas.core.typedef import ClassificationTypeDef

def check_resp(method, resp):
    print(json.dumps(resp, indent=2))
    _ = input(f">>>{method}")

if __name__ == "__main__":
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME"),
        authentication=cred
    )

    ## Set up
    ctd = ClassificationTypeDef("my_custom_classif")

    resp = client.get_all_typedefs()
    check_resp("get_all_typedefs",list(resp.keys()))

    # X upload_typedefs where we force update uses a get method
    resp=client.upload_typedefs(classificationDefs = [ctd], force_update=True)
    check_resp("upload_typedefs",resp)

    



    # SETUP
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demoinput01",
        guid="-100"
    )
    output01 = AtlasEntity(
        name="output01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://demooutput01",
        guid="-101"
    )
    output01.addClassification(AtlasClassification("my_custom_classif"))
    process = AtlasProcess(
        name="sample process",
        typeName="Process",
        qualified_name="pyapacheatlas://democustomprocess",
        inputs=[input01],
        outputs=[output01],
        guid="-102"
    )

    # Convert the individual entities into json before uploading.
    results = client.upload_entities(
        batch=[output01, input01, process]
    )
    out01_guid = results["guidAssignments"]["-101"]

    resp = client.get_entity(out01_guid)
    check_resp("get_entity", resp)
    resp = client.get_single_entity(out01_guid)
    check_resp("get_single_entity", resp)
    relationship_guid = resp["entity"]["relationshipAttributes"]["outputFromProcesses"][0]["relationshipGuid"]

    resp = client.get_entity_header(guid=out01_guid)
    check_resp("get_entity_header", resp)

    resp = client.get_entity_classification(out01_guid, "my_custom_classif")
    check_resp("get_entity_classification", resp)
    resp = client.get_entity_classifications(out01_guid)
    check_resp("get_entity_classifications", resp)

    resp = client.get_entity_lineage(out01_guid)
    check_resp("get_entity_lineage", resp)
    resp = client.get_entity_next_lineage(out01_guid, "INPUT")
    check_resp("get_entity_next_lineage", resp)

    resp = client.get_relationship(relationship_guid)
    check_resp("get_relationship", resp)

    resp = client.collections.list_collections()
    check_resp("list_collections", [r for r in resp]) # Generator

    glossaryResp = client.glossary.get_glossary()
    check_resp("get_glossary", glossaryResp)

    if "blah" not in [g["displayText"] for g in glossaryResp["terms"]]:
        termResp = client.glossary.upload_term(AtlasGlossaryTerm(name="blah", qualifiedName="blah@Glossary", glossaryGuid=glossaryResp["guid"]))
        termRespGuid = termResp["guid"]
    else:
        termRespGuid = [g["termGuid"] for g in glossaryResp["terms"] if g["displayText"] == "blah"][0]

    resp = client.glossary.get_term(termRespGuid)
    check_resp("get_term", resp)

    termAssignedResp = client.glossary.get_termAssignedEntities(termRespGuid)
    check_resp("get_termAssignedEntities", termAssignedResp)

    # TODO import_terms_status
