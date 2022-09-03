import json
import os
import time

from azure.identity import AzureCliCredential
from pyapacheatlas.core import AtlasEntity, AtlasProcess, PurviewClient
from pyapacheatlas.core.entity import AtlasClassification
from pyapacheatlas.core.glossary.term import AtlasGlossaryTerm
from pyapacheatlas.core.typedef import AtlasAttributeDef, AtlasStructDef, ClassificationTypeDef, EntityTypeDef, TypeCategory

def check_resp(method, resp):
    print(json.dumps(resp, indent=2))
    _ = input(f">>>{method}")

if __name__ == "__main__":
    cred = AzureCliCredential()
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME"),
        authentication=cred
    )

    # SETUP
    etd = EntityTypeDef("custom_entity_def_delete")
    ctd = ClassificationTypeDef("my_custom_classif_put")
    bmd = AtlasStructDef(
        name="biz_meta_delete",
        category=TypeCategory.BUSINESSMETADATA,
        attributeDefs=[
            AtlasAttributeDef(name="foo",options={"maxStrLength": "500","applicableEntityTypes":"[\"DataSet\"]"})
        ]
    )

    resp=client.upload_typedefs(entityDefs=[etd],classificationDefs = [ctd], 
        businessMetadataDefs=[bmd], 
        force_update=True
    )

    glossaryResp = client.glossary.get_glossary()

    if "blahDelete" not in [g["displayText"] for g in glossaryResp["terms"]]:
        termResp = client.glossary.upload_term(AtlasGlossaryTerm(name="blahDelete", qualifiedName="blahDelete@Glossary", glossaryGuid=glossaryResp["guid"]))
        termRespGuid = termResp["guid"]
    else:
        termRespGuid = [g["termGuid"] for g in glossaryResp["terms"] if g["displayText"] == "blah"][0]

    
    input01 = AtlasEntity(
        name="input01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://smoke_put_01",
        guid="-100"
    )
    output01 = AtlasEntity(
        name="output01",
        typeName="DataSet",
        qualified_name="pyapacheatlas://smoke_put_02",
        guid="-101"
    )
    output01.addBusinessAttribute(biz_meta_delete={"foo":"abc"})
    process = AtlasProcess(
        name="sample process",
        typeName="Process",
        qualified_name="pyapacheatlas://smoke_put_03",
        inputs=[input01],
        outputs=[output01],
        guid="-102"
    )
    entity_upload_results = client.upload_entities(
        batch=[output01, input01, process]
    )
    out01_guid = entity_upload_results["guidAssignments"]["-101"]
    _ = client.glossary.assignTerm([{"guid":out01_guid}], termRespGuid)

    try:
        add_classif_resp = client._classify_entity_adds(out01_guid, [AtlasClassification("my_custom_classif_put").to_json()])
    except Exception as e:
        pass
    time.sleep(5)
    update_classif_resp = client._classify_entity_updates(out01_guid, [AtlasClassification("my_custom_classif_put").to_json()])
    check_resp("update classification entity", update_classif_resp)

    resp = client.get_single_entity(out01_guid)
    out01_entity = resp["entity"]
    relationship_guid = resp["entity"]["relationshipAttributes"]["outputFromProcesses"][0]["relationshipGuid"]

    # PUT TESTS
    resp = client.partial_update_entity(out01_guid, attributes = {"name":"blah"})
    check_resp("partial update with guid", resp)

    resp = client.partial_update_entity(typeName="DataSet", qualifiedName="pyapacheatlas://smoke_put_02",attributes = {"name":"blah2"})
    check_resp("partial update with type, qn", resp)

    resp = client.upload_typedefs(
        entityDefs=[
            EntityTypeDef("custom_entity_def_delete", attributes=[AtlasAttributeDef("bar")])
        ],
        force_update=True
    )
    check_resp("upload_typedefs with force update", resp)

    
    resp = client.delete_entity(list(entity_upload_results["guidAssignments"].values()))
    check_resp("delete_entity", resp)
    
    # TODO update_entity_labels

    