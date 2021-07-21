from datetime import datetime
import json
import os
from uuid import uuid4

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess, AtlasClassification


def does_this_asset_have_updates(asset):
    # If there is an updatedBy field and it's a ServiceAdmin, no update has occurred
    # This assumes the Purview Service doesn't allow automated updates after
    # a person has touched the service
    if "updatedBy" not in asset or asset["updatedBy"] == "ServiceAdmin":
        return None

    updates = {}
    # So there is an update, now grab the fields you care about

    if "classifications" in asset:
        # There is no way to tell if a human added the classification or not
        # Have to take them all
        updates["classifications"] = [AtlasClassification(c["typeName"]) for c in asset["classifications"]]

    if "relationshipAttributes" in asset and "meanings" in asset["relationshipAttributes"]:
        # We know that a human did this since Purview can't currently make
        # this meaning automatically
        old_term_displayText = [t["displayText"]
                                for t in asset["relationshipAttributes"]["meanings"]]
        updates["terms"] = old_term_displayText

    if "contacts" in asset:
        updates["contacts"] = asset["contacts"]

    if "attributes" in asset and "description" in asset["attributes"]:
        updates["description"] = asset["attributes"]["description"]

    # Assuming that we've caught all of the elements we want to update
    # If they've been added to the updates variable, we need to identify
    # the type and its qualified name as well.
    if len(updates) > 0:
        updates["qualifiedName"] = asset["attributes"]["qualifiedName"]
        updates["typeName"] = asset["typeName"]
        updates["guid"] = asset["guid"]

    return updates


if __name__ == "__main__":
    """
    """

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("AZURE_TENANT_ID", ""),
        client_id=os.environ.get("AZURE_CLIENT_ID", ""),
        client_secret=os.environ.get("AZURE_CLIENT_SECRET", "")
    )
    client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    new_client = PurviewClient(
        account_name=os.environ.get("NEW_PURVIEW_NAME", ""),
        authentication=oauth
    )

    # print(json.dumps(client.get_glossary(),indent=2))
    # exit()
    # print(json.dumps(client.get_glossary_term("312572ce-cab6-4de3-bbc8-acd9551df1f8"),indent=2))
    # exit()
    # print(json.dumps(client.get_entity("bd53e412-0d08-442f-a8da-2286b97aac3a"),indent=2))
    # exit()

    batch_path = "./batches"
    already_processed = []
    if not os.path.exists(batch_path):
        os.mkdir(batch_path)

    for filename in os.listdir(batch_path):
        complete_path = os.path.join(batch_path, filename)
        if os.path.getsize(complete_path) == 0:
            continue
        with open(complete_path, 'r') as fp:
            already_processed.extend(json.load(fp))

    # Execute a search across all entities
    search_generator = client.search_entities(
        query="sql_sensitive_table", limit=100)

    # Collect a batch of 100 entities and process updates
    search_results_queue = []
    old_guids_processed_this_execution = []
    try:
        for search_result in search_generator:
            # Add the result to the queue
            guid = search_result["id"]
            if guid in already_processed:
                continue

            search_results_queue.append(guid)
            # if len(search_results_queue) < 100:
            #     continue

            # Thing that needs to get done each batch

            # The search queue is at 100
            # Get all of those entities and their referenced entities
            get_results = client.get_entity(search_results_queue)

            # TODO: Need to handle tabular schemas
            referred_entities = list(get_results["referredEntities"].values())
            direct_entities = get_results["entities"]

            for entity in referred_entities + direct_entities:
                partialEntity = does_this_asset_have_updates(entity)
                if not partialEntity:
                    continue

                # Inefficient
                new_entity_response = new_client.get_entity(
                    typeName=partialEntity["typeName"],
                    qualifiedName=partialEntity["qualifiedName"]
                )
                newest_entity = new_entity_response["entities"][0]
                # Drop fields that aren't valid for an upload
                for badKey in ["lastModifiedTS", "status", "createdBy", "updatedBy", "createTime", "updateTime", "verison"]:
                    if badKey in newest_entity:
                        newest_entity.pop(badKey)
                newest_entity_original_guid = newest_entity["guid"]
                newest_entity["guid"] = "-1"

                updates_to_newest_entity = {}

                newest_entity["relationshipAttributes"] = {}
                # for relAttrib, relValue in newest_entity["relationshipAttributes"].items():
                #     if not relValue:
                #         continue
                #     if isinstance(relValue, list):
                #         updates_to_newest_entity[relAttrib] = [{"guid":x["guid"]} for x in relValue]
                #     else:
                #         updates_to_newest_entity[relAttrib] = {"guid": relValue["guid"]}

                # newest_entity["relationshipAttributes"].update(updates_to_newest_entity)
                # print(json.dumps(newest_entity,indent=2))

                # contacts
                # Have to do a whole update
                if "contacts" in partialEntity:
                    newest_entity["contacts"] = partialEntity["contacts"]
                    # While we're here, update the description if necessary!
                    if "description" in partialEntity:
                        newest_entity["attributes"]["description"] = partialEntity["description"]
                    # All the fields are updated, do an upload!
                    payload = {"entities": [newest_entity]}
                    upload_results = new_client.upload_entities(batch=payload)

                elif "description" in partialEntity:
                    new_client.partial_update_entity(
                        typeName=partialEntity["typeName"],
                        qualifiedName=partialEntity["qualifiedName"],
                        attributes={
                            "description": partialEntity["description"]}
                    )

                # One offs
                # Classifications
                if "classifications" in partialEntity:

                    print(partialEntity["classifications"])

                    new_client.classify_entity(
                        guid=newest_entity_original_guid,
                        classifications=partialEntity["classifications"],
                        # This makes this slower (a second API call) but could
                        # be improved by looking at newest_entity
                        force_update=True
                    )
                # Terms
                if "terms" in partialEntity:
                    for term in partialEntity["terms"]:
                        new_client.assignTerm(
                            entities=[{"guid": newest_entity_original_guid}],
                            termName=term
                        )
                old_guids_processed_this_execution.append(
                    partialEntity["guid"])
    finally:
        # Always write out the batch so we know where we left off
        when = (datetime.utcnow().isoformat()[:-3] + 'Z').replace(":", "-")
        batch_guid = str(uuid4())
        with open(os.path.join(batch_path, when+batch_guid+'.json'), 'w') as fp:
            json.dump(old_guids_processed_this_execution, fp)
