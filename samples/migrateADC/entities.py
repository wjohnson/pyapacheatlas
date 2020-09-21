from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core import AtlasClient
from migrate_util import discover_guids, remap_guids, export_records
import argparse
import configparser
import os
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

config = configparser.ConfigParser()
config.read("./samples/migrateADC/config.ini")

folder_path = config["Default"]["EntitiesFolder"]
output_path = config["Default"]["EntitiesRemapped"]

relationships_guid_path = config["Default"]["EntitiesRelationships"]
old_to_new_entities_guid_path = config["Default"]["EntitiesOldToNew"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                        help="Use if you've already written the entities to disk.")
    args = parser.parse_args()

    oauth_old = ServicePrincipalAuthentication(
        tenant_id=config["OldClient"]["TENANT_ID"],
        client_id=config["OldClient"]["CLIENT_ID"],
        client_secret=config["OldClient"]["CLIENT_SECRET"]
    )
    old_client = AtlasClient(
        endpoint_url=config["OldClient"]["ENDPOINT_URL"],
        authentication=oauth_old
    )
    oauth_new = ServicePrincipalAuthentication(
        tenant_id=config["NewClient"]["TENANT_ID"],
        client_id=config["NewClient"]["CLIENT_ID"],
        client_secret=config["NewClient"]["CLIENT_SECRET"]
    )
    new_client = AtlasClient(
        endpoint_url=config["NewClient"]["ENDPOINT_URL"],
        authentication=oauth_new
    )

    gt = GuidTracker(starting=-50000)
    # Get all the types you want to "export"
    list_of_types_to_consider = [
        "demo_column", "demo_table", "demo_table_columns", "demo_process",
        "demo_column_lineage"
    ]

    indicators = ["guid"]

    # Export the list of types to consider
    if not args.skip_download:
        print("Searching through entities")
        export_records(old_client, folder_path, list_of_types_to_consider)

    # Discover the Relationship Guids that will be uploaded later
    print("Discovering guids to remap from disk")
    relationship_guids = discover_guids(folder_path, ["relationshipGuid"])
    with open(relationships_guid_path, 'a+') as fp:
        for relationship in relationship_guids:
            fp.write(relationship)
            fp.write("\n")

    # Get Guids and replace them
    print("Remapping guids from disk and into memory")
    old_entity_guids = discover_guids(folder_path, indicators)
    orig_guid_to_temp_guid = {g: str(gt.get_guid()) for g in old_entity_guids}
    remapped_entities = remap_guids(
        orig_guid_to_temp_guid, folder_path, output_path)

    print("Processing entities in memory")
    for entity in remapped_entities:
        # Strip the relationshipAttributes, they will be added later.
        entity["relationshipAttributes"] = {}
        entity.pop("lastModifiedTS")
        entity.pop("createdBy")
        entity.pop("updatedBy")
        entity.pop("createTime")
        entity.pop("updateTime")

    input("Ready to upload entities. Continue?  Ctrl + C to back out now.")
    # Upload and get results["guidAssignments"] for new guids
    results = new_client.upload_entities(batch=remapped_entities)

    # Map old guids to new guids
    temp_guid_to_old_guid = {v: k for k, v in orig_guid_to_temp_guid.items()}

    old_guid_to_new_guid = dict()
    for temp_guid, old_guid in temp_guid_to_old_guid.items():
        if temp_guid in results["guidAssignments"]:
            old_guid_to_new_guid[old_guid] = results["guidAssignments"][temp_guid]
    with open(old_to_new_entities_guid_path, 'w') as fp:
        json.dump(old_guid_to_new_guid, fp)

    print("Completed program")
