from audioop import mul
import json
import os
from tabnanny import check
import time

from azure.identity import AzureCliCredential
from pyapacheatlas.core import AtlasEntity, AtlasProcess, PurviewClient
from pyapacheatlas.core.entity import AtlasClassification
from pyapacheatlas.core.glossary import term
from pyapacheatlas.core.glossary.term import AtlasGlossaryTerm
from pyapacheatlas.core.typedef import AtlasAttributeDef, AtlasStructDef, ClassificationTypeDef, EntityTypeDef, TypeCategory
from pyapacheatlas.core.util import AtlasException

def check_resp(method, resp):
    print(json.dumps(resp, indent=2))
    _ = input(f">>>{method}")

if __name__ == "__main__":
    PURVIEW_ACCT_NAME = os.environ.get("PURVIEW_NAME")
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name=PURVIEW_ACCT_NAME,
        authentication=cred
    )

    # SETUP
    etd = EntityTypeDef("custom_entity_def_post")
    ctd = ClassificationTypeDef("my_custom_classif_post")
    ctd2 = ClassificationTypeDef("my_custom_classif_post_bulk")
    bmd = AtlasStructDef(
        name="biz_meta_post",
        category=TypeCategory.BUSINESSMETADATA,
        attributeDefs=[
            AtlasAttributeDef(name="foo",options={"maxStrLength": "500","applicableEntityTypes":"[\"DataSet\"]"})
        ]
    )

    resp=client.upload_typedefs(entityDefs=[etd],classificationDefs = [ctd, ctd2], 
        businessMetadataDefs=[bmd], 
        force_update=True
    )

    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://smoke_post_01",
        guid="-100"
    )
    output01 = AtlasEntity(
        name="output01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://smoke_post_02",
        guid="-101"
    )
    output01.addBusinessAttribute(biz_meta_delete={"foo":"abc"})
    process = AtlasProcess(
        name="sample process",
        typeName="Process",
        qualified_name="pyapacheatlas://smoke_post_03",
        inputs=[input01],
        outputs=[output01],
        guid="-102"
    )
    entity_upload_results = client.upload_entities(
        batch=[output01, input01, process]
    )
    check_resp("upload_entities", entity_upload_results)
    out01_guid = entity_upload_results["guidAssignments"]["-101"]
    in01_guid = entity_upload_results["guidAssignments"]["-100"]

    resp = client.get_single_entity(out01_guid)
    out01_entity = resp["entity"]
    relationship_guid = resp["entity"]["relationshipAttributes"]["outputFromProcesses"][0]["relationshipGuid"]

    # POST TESTS

    # Type Definition
    etd2 = EntityTypeDef("custom_entity_def_delete_new")
    resp = client.upload_typedefs(entityDefs=[etd2])
    check_resp("upload_typedefs not force update", resp)
    _ = client.delete_type("custom_entity_def_delete_new")

    # Bulk Entities as batch
    batch_resp = client.upload_entities(
        [AtlasEntity("n1", "DataSet", "postTest1", "-1"),
        AtlasEntity("n2", "DataSet", "postTest2", "-2"),
        AtlasEntity("n3", "DataSet", "postTest3", "-3")
        ],
        batch_size=2
    )
    check_resp("upload_entities with batch size", batch_resp)
    batch_resp_guids = (
        list(batch_resp[0]["guidAssignments"].values()) +
        list(batch_resp[1]["guidAssignments"].values())
    )
    _ = client.delete_entity(batch_resp_guids)

    # Bulk Classification
    try:
        resp = client.classify_bulk_entities(
            list(entity_upload_results["guidAssignments"].values()),
            AtlasClassification("my_custom_classif_post_bulk")
        )
        check_resp("classify_bulk_entites", resp)
    except AtlasException as e:
        print("Classify Bulk Entities had an Atlas Exception but at least it posted")

    # Assign Classification
    try:
        resp = client._classify_entity_adds(out01_guid, [AtlasClassification("my_custom_classif_post").to_json()])
        check_resp("_classify_entity_adds", resp)
    except AtlasException as e:
        print("Classify Entity Adds had an Atlas Exception but at least it posted")
    
    # Add a glossary Term
    glossaryResp = client.glossary.get_glossary()
    matchingTerms = [g["termGuid"] for g in glossaryResp["terms"] if g["displayText"] == "blahPost"]
    if len(matchingTerms) > 0:
        assignments = client.glossary.get_termAssignedEntities(matchingTerms[0])
        client.glossary.delete_assignedTerm(assignments, matchingTerms[0])
        time.sleep(5)
        client.glossary.delete_term(matchingTerms[0])
    
    singleTermUploadresp = client.glossary.upload_term(AtlasGlossaryTerm(name="blahPost", qualifiedName="blahPost@Glossary", glossaryGuid=glossaryResp["guid"]))
    check_resp("upload_term", singleTermUploadresp)

    assignTermResp = client.glossary.assignTerm([{"guid":in01_guid}], singleTermUploadresp["guid"] )
    check_resp("assignTerm", assignTermResp)

    latest_input01 = [client.get_single_entity(in01_guid)["entity"]]

    client.glossary.delete_assignedTerm(latest_input01, singleTermUploadresp["guid"])
    time.sleep(5)
    client.glossary.delete_term(singleTermUploadresp["guid"])

    # Add many glossary terms
    try:
        multiTermUploadresp = client.glossary.upload_terms(
            [
                AtlasGlossaryTerm(name="blahPost2", qualifiedName="blahPost2@Glossary", glossaryGuid=glossaryResp["guid"]),
                AtlasGlossaryTerm(name="blahPost3", qualifiedName="blahPost3@Glossary", glossaryGuid=glossaryResp["guid"])
            ]
        )
        check_resp("upload_terms", multiTermUploadresp)
    except AtlasException as e:
        print("Upload terms had an exception but at least it posted")
        multiTermUploadresp = [client.glossary.get_term(name="blahPost2")]
        if len(multiTermUploadresp) == 0 or multiTermUploadresp[0] == None:
            multiTermUploadresp = [client.glossary.upload_term(AtlasGlossaryTerm(name="blahPost2", qualifiedName="blahPost2@Glossary", glossaryGuid=glossaryResp["guid"]))]

    # Import terms
    glossaryResp = client.glossary.get_glossary()
    templateHeader = ["Name", "Nick Name", "Status", "Definition",
    "Acronym", "Resources", "Related Terms", "Synonyms", "Stewards",
    "Experts", "Parent Term Name", "IsDefinitionRichText", "Term Template Names"]
    templateBody = ["blahFromImportPost", "", "Draft", "This is a def",
    "", "", "", "", "",
    "", "", "True", "System default"
    ]
    with open("./temp.csv", 'w') as fp:
        fp.write(','.join(templateHeader))
        fp.write("\n")
        fp.write(','.join(templateBody))
        fp.write("\n")
    
    try:
        resp = client.glossary.import_terms("./temp.csv", glossary_guid=glossaryResp["guid"])
        check_resp("import_terms", resp)
    except AtlasException as e:
        print("import terms had an atlas exception but at least it posted")

    try:
        _ = client.glossary.export_terms([multiTermUploadresp[0]["guid"]], "./temp-export.csv", glossary_guid=glossaryResp["guid"])
        if os.path.exists("./temp-export.csv"):
            os.remove("./temp-export.csv")
        else:
            raise Exception("Failed to write ./temp-export.csv")
    except AtlasException as e:
        print("export terms had an atlas exception but at least it posted")

    # Upload Relationship
    try:
        resp = client.upload_relationship(
            {
                "typeName": "AtlasGlossarySemanticAssignment",
                "attributes": {},
                "guid": "-100",
                "end1": {
                    "guid": multiTermUploadresp[0]["guid"],
                    "typeName": "AtlasGlossaryTerm"
                },
                "end2": {
                    "guid": out01_guid
                }
            }
        )
        check_resp("upload_relationship", resp)
    except AtlasException as e:
        print("upload_relationship hit an AtlasException but at least it posted")

    resp = client.update_businessMetadata(
        in01_guid,
        {"biz_meta_post": {"foo":"abc"}},
        force_update=True
        )
    check_resp("update_businessMetadata", resp)
    

    resp = client.discovery.autocomplete("blah")
    check_resp("autocomplete", resp)

    resp = client.discovery.browse("DataSet")
    check_resp("browse", resp)

    resp = client.discovery.suggest("blah")
    check_resp("suggest", resp)
    
    # Collections
    all_collections = [l for l in client.collections.list_collections()]
    collect_friendlynames = [l["friendlyName"] for l in all_collections]
    if "postTest" in collect_friendlynames:
        new_collection_id = [l["name"] for l in all_collections if l["friendlyName"] == "postTest"][0]
    else:
        createResp = client.collections.create_or_update_collection(
            name="456post", friendlyName="postTest",
            parentCollectionName=PURVIEW_ACCT_NAME,
            
        )
        new_collection_id = createResp["name"]

    cEnt = AtlasEntity("forColl", "DataSet","forCol1", "-1")
    collectionSingleEntity = client.collections.upload_single_entity(cEnt, new_collection_id)
    check_resp("collection single entity", collectionSingleEntity)

    cEnt2 = AtlasEntity("forCol2", "DataSet","forCol2", "-2")
    cEnt3 = AtlasEntity("forCol3", "DataSet","forCol3", "-3")

    collectionMultiEntity = client.collections.upload_entities(
        batch=[cEnt2, cEnt3], collection=new_collection_id
    )
    check_resp("collection entities", collectionMultiEntity)

    moveResp = client.collections.move_entities([in01_guid], collection=new_collection_id)
    check_resp("move entities", moveResp)
        
    # TODO force_update for update_entity_labels

    # Clean up
    
    ### Cleanup these terms
    for termResp in multiTermUploadresp:
        termX = client.glossary.get_termAssignedEntities(termResp["guid"])
        if len(termX) > 0:
            client.glossary.delete_assignedTerm(termX, termResp["guid"])
            time.sleep(3)
        client.glossary.delete_term(termResp["guid"])

    entities_made = (
        list(entity_upload_results["guidAssignments"].values()) + 
        list(collectionMultiEntity["guidAssignments"].values()) + 
        list(collectionSingleEntity["guidAssignments"].values())
    )
    resp = client.delete_entity(entities_made)

    check_resp("delete_entity", resp)

    

    