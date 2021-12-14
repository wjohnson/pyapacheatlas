import argparse
from datetime import datetime
import json
import logging
import os
from uuid import uuid4

# PyApacheAtlas packages
# Connect to Atlas via a Service Principal
from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess, AtlasClassification


def unique_file_name():
    when = (datetime.utcnow().isoformat()[:-3] + 'Z').replace(":", "-")
    batch_guid = str(uuid4())
    return when+batch_guid+'.json'


def log_completed_updates(batch_path, guids_to_log):
    batch_log_path = os.path.join(batch_path, unique_file_name())
    with open(batch_log_path, 'w') as fp:
        json.dump(guids_to_log, fp)
    logging.info("Completed writing batch history at: " + batch_log_path)


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
        updates["classifications"] = [AtlasClassification(
            c["typeName"]) for c in asset["classifications"]]

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
    This sample provides a means of 'partially' migrating an Azure Purview
    services changes to another Azure Purview service that has scanned
    the same data sources. It supports overwriting Contacts (experts, owners),
    descriptions, appending classifications, and appending glossary terms to
    assets that exist in both services.

    This sample is useful for those who have invested time in annotating
    an existing Purview service but want to move those updates to a
    different catalog. This sample should not be used on a regular basis
    to move annotations, instead Stewards should have annotate the true
    Purview service rather than maintaining multiple Purview services.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--search", help="The search term to search. Leave blank if working on existing search results.")
    parser.add_argument(
        "--search-folder", help="The folder to store search results.", default="./searches")
    parser.add_argument(
        "--batch-folder", help="The folder to store batching results, used to avoid repeating same operations.", default="./batches")
    parser.add_argument(
        "-v", help="Set the logging level to INFO", action="store_true"
    )
    parser.add_argument(
        "-vv", help="Set the logging level to DEBUG", action="store_true"
    )
    args, _ = parser.parse_known_args()

    if args.vv:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.v:
        logging.getLogger().setLevel(logging.INFO)

    # Authenticate against your Atlas server
    oauth = ServicePrincipalAuthentication(
        tenant_id=os.environ.get("AZURE_TENANT_ID", ""),
        client_id=os.environ.get("AZURE_CLIENT_ID", ""),
        client_secret=os.environ.get("AZURE_CLIENT_SECRET", "")
    )
    old_client = PurviewClient(
        account_name=os.environ.get("PURVIEW_NAME", ""),
        authentication=oauth
    )

    new_client = PurviewClient(
        account_name=os.environ.get("NEW_PURVIEW_NAME", ""),
        authentication=oauth
    )

    # TODO: Updates this to be either a folder or list of files
    search_path = args.search_folder
    batch_path = args.batch_folder
    to_be_processed = []
    already_processed = []

    if not os.path.exists(batch_path):
        os.mkdir(batch_path)
    if not os.path.exists(search_path):
        os.mkdir(search_path)

    # Drain the search engine for the passed in search term
    if args.search:
        total_search_results = 0
        # Execute a search across all entities
        search_generator = old_client.discovery.search_entities(
            query=args.search, limit=100
        )
        batch_size = 100
        search_batch = []
        search_filename = unique_file_name()

        for entity in search_generator:
            search_batch.append(entity["id"])
            total_search_results += 1
            if len(search_batch) == batch_size:
                with open(os.path.join(search_path, unique_file_name()), 'w') as search_fp:
                    json.dump(search_batch, search_fp)
                search_batch = []

        # Dealing with the remainder of searches
        if len(search_batch) > 0:
            with open(os.path.join(search_path, unique_file_name()), 'w') as search_fp:
                json.dump(search_batch, search_fp)
            search_batch = []
        logging.info("Total Search Results: "+str(total_search_results))

    # Now into the main execution, where we want to actually pick up the work
    # that needs to be done.
    # Collect all the searches to be executed
    for filename in os.listdir(search_path):
        complete_path = os.path.join(search_path, filename)
        if os.path.getsize(complete_path) == 0:
            continue
        with open(complete_path, 'r') as fp:
            to_be_processed.extend(json.load(fp))

    # Collect all the guids we've seen in the old client
    for filename in os.listdir(batch_path):
        complete_path = os.path.join(batch_path, filename)
        if os.path.getsize(complete_path) == 0:
            continue
        with open(complete_path, 'r') as fp:
            already_processed.extend(json.load(fp))

    # Reduce the set of to_be_processed by eliminating those seen already
    logging.info(
        f"Original number of searched entities to be processed: {len(to_be_processed)}")
    to_be_processed = list(set(to_be_processed).difference(already_processed))
    logging.info(
        f"Reduced set of entities to be processed: {len(to_be_processed)}")

    # Iterate over all of the entities to be processed in batches of 100
    search_results_offset = 0
    _stepsize = 100
    old_guids_processed_this_execution = []

    # Wrapping this all in a try finally statement to be sure
    # we can restart and not have too many redos
    try:
        work_min = search_results_offset - _stepsize

        while search_results_offset < len(to_be_processed):
            logging.debug("Iterating at offset: " + str(search_results_offset))
            to_be_processed_batch = to_be_processed[search_results_offset:(
                search_results_offset+_stepsize)]

            get_results = old_client.get_entity(to_be_processed_batch)
            # Update the offset
            search_results_offset = search_results_offset + _stepsize

            referred_entities = list(get_results["referredEntities"].values())
            direct_entities = get_results["entities"]
            # Handling tabular schemas referenced
            tabular_schema_columns = []
            tabular_schema_guids = [
                t["guid"] for t in referred_entities if t["typeName"] == "tabular_schema"]
            tabular_schema_guids.extend([t["relationshipAttributes"]["tabular_schema"]["guid"] for t in direct_entities if t.get(
                'relationshipAttributes', {}).get('tabular_schema', None)])
            if tabular_schema_guids:
                tabular_results = old_client.get_entity(tabular_schema_guids)
                if "referredEntities" in tabular_results:
                    tabular_schema_columns = list(
                        tabular_results["referredEntities"].values())

            # Perform an update for every entity, could be more efficient in bulk
            for entity in referred_entities + tabular_schema_columns + direct_entities:
                if entity["guid"] in already_processed:
                    logging.debug(
                        "Skipping the entity due to already processed: "+entity["guid"])
                    continue

                partialEntity = does_this_asset_have_updates(entity)
                if not partialEntity:
                    logging.debug(
                        "Skipping the entity due to no changes: "+entity["guid"])
                    old_guids_processed_this_execution.append(entity["guid"])
                    continue

                # Inefficient, this should be a larger call to get entity
                # with all of the same types if possible
                logging.debug(
                    f"On destination client getting {partialEntity['qualifiedName']}")
                new_entity_response = new_client.get_entity(
                    typeName=partialEntity["typeName"],
                    qualifiedName=partialEntity["qualifiedName"]
                )

                if not new_entity_response:
                    logging.warn(
                        "Entity does not exist on target but contains changes: " + entity["guid"])
                    old_guids_processed_this_execution.append(entity["guid"])
                    continue
                newest_entity = new_entity_response["entities"][0]
                newest_entity_original_guid = newest_entity["guid"]
                # This needs to be a negative number for /entity/bulk upload
                newest_entity["guid"] = "-1"

                # Blank out the relationship attributes to avoid complexity of
                # keeping references to the new guids
                newest_entity["relationshipAttributes"] = {}
                # Alternatively, keep the attributes around, but simplify to just guid
                # updates_to_newest_entity = {}
                # for relAttrib, relValue in newest_entity["relationshipAttributes"].items():
                #     if not relValue:
                #         continue
                #     if isinstance(relValue, list):
                #         updates_to_newest_entity[relAttrib] = [{"guid":x["guid"]} for x in relValue]
                #     else:
                #         updates_to_newest_entity[relAttrib] = {"guid": relValue["guid"]}

                # newest_entity["relationshipAttributes"].update(updates_to_newest_entity)

                # contacts
                # Have to do a whole update
                if "contacts" in partialEntity:
                    logging.debug(f"{partialEntity['guid']} Found contacts")
                    newest_entity["contacts"] = partialEntity["contacts"]
                    # While we're here, update the description if necessary!
                    if "description" in partialEntity:
                        logging.debug(
                            f"{partialEntity['guid']} Found description too")
                        newest_entity["attributes"]["description"] = partialEntity["description"]
                    # All the fields are updated, do an upload!
                    # This works because the referenced entities are omitted
                    payload = {"entities": [newest_entity]}
                    # Inefficient, could be a much larger batch
                    upload_results = new_client.upload_entities(batch=payload)

                elif "description" in partialEntity:
                    logging.debug(
                        f"{partialEntity['guid']} No contacts but there was a description")
                    # If there are other attributes, you could add them here
                    new_client.partial_update_entity(
                        typeName=partialEntity["typeName"],
                        qualifiedName=partialEntity["qualifiedName"],
                        attributes={
                            "description": partialEntity["description"]}
                    )

                # One offs
                # Classifications
                if "classifications" in partialEntity:
                    logging.debug(
                        f"{partialEntity['guid']} Found classifications")
                    new_client.classify_entity(
                        guid=newest_entity_original_guid,
                        classifications=partialEntity["classifications"],
                        # This makes this slower (a second API call) but could
                        # be improved by looking at newest_entity to determine
                        # if the classifications already existed
                        force_update=True
                    )
                # Terms
                if "terms" in partialEntity:
                    logging.debug(f"{partialEntity['guid']} Found terms")
                    for term in partialEntity["terms"]:
                        logging.debug(
                            f"{partialEntity['guid']} Adding term: "+term)
                        # Inefficient, instead you could list all of the entities
                        # getting this classification, but likely it's rare to
                        # have a large batch of entities with the same term
                        new_client.glossary.assignTerm(
                            entities=[{"guid": newest_entity_original_guid}],
                            termName=term
                        )
                old_guids_processed_this_execution.append(
                    partialEntity["guid"])
            # Out of the inner for loop, still in while loop
            log_completed_updates(
                batch_path, old_guids_processed_this_execution)
            already_processed.extend(old_guids_processed_this_execution)
            old_guids_processed_this_execution = []
    finally:
        # Always write out the batch so we know where we left off
        log_completed_updates(batch_path, old_guids_processed_this_execution)

print("Completed successfully!")
