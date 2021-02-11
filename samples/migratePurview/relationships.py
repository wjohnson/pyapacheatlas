import argparse
import configparser
import json
import os
import sys

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core import AtlasClient

from migrate_util import discover_guids, remap_guids, export_records

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

config = configparser.ConfigParser()
config.read("./samples/migratePurview/config.ini")

output_path = config["Default"]["RelationshipsRemapped"]
relationships_path = config["Default"]["RelationshipsFolder"]

glossary_relationships = config["Default"]["GlossaryRelationships"]
entity_relationships = config["Default"]["EntitiesRelationships"]

old_to_new_entities_guid_path = config["Default"]["EntitiesOldToNew"]
old_to_new_glossary_guid_path = config["Default"]["GlossaryOldToNew"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                        help="Use if you've already written the relationships to disk.")
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

    # Load the discovered relationships
    relationship_guids = set()
    with open(glossary_relationships, 'r') as fp:
        _temp_relationship_guids = fp.readlines()
        relationship_guids = relationship_guids.union(_temp_relationship_guids)
    with open(entity_relationships, 'r') as fp:
        _temp_relationship_guids = fp.readlines()
        relationship_guids = relationship_guids.union(_temp_relationship_guids)

    relationship_guids = [r.strip() for r in relationship_guids]
    print(f"Working with {len(relationship_guids)} relationships")

    # Load the existing relationships
    old_to_new_guids = dict()
    with open(old_to_new_entities_guid_path, 'r') as fp:
        _temp = json.load(fp)
        old_to_new_guids.update(_temp)

    with open(old_to_new_glossary_guid_path, 'r') as fp:
        _temp = json.load(fp)
        old_to_new_guids.update(_temp)
    print(f"Working with {len(old_to_new_guids)} relationship mappings")

    if not args.skip_download:
        print("Downloading relationships data")
        # Query the relationships
        # This will take a while...
        buffer = []
        counter = 0
        for guid in relationship_guids:
            relationship_entity = old_client.get_relationship(guid)
            buffer.append(relationship_entity)
            if len(buffer) > 100:
                with open(os.path.join(relationships_path, f"batch-{counter}.json"), 'w') as fp:
                    json.dump(buffer, fp)
                buffer = []
                counter = counter + 1

        if len(buffer) > 0:
            with open(os.path.join(relationships_path, f"batch-last.json"), 'w') as fp:
                json.dump(buffer, fp)

    # Now we can read load the remapping files and
    # Load in the remapping files
    print('Remapping guids')
    remapped_relationships = remap_guids(
        old_to_new_guids, relationships_path, output_path)

    # Clean up the remapped relationship and upload one by one...
    # This will take a while...
    gt = GuidTracker()
    counter = 0
    skipped = 0
    total_relationships = len(remapped_relationships)
    for relationship in remapped_relationships:
        inner_relationship = relationship["relationship"]
        inner_relationship["guid"] = str(gt.get_guid())
        # Pop attributes that break the upload
        inner_relationship.pop("updateTime")
        inner_relationship.pop("lastModifiedTS")
        inner_relationship.pop("updatedBy")
        inner_relationship.pop("createTime")
        inner_relationship.pop("createdBy")
        counter = counter + 1
        try:
            results = new_client.upload_relationship(inner_relationship)
        except Exception as e:
            with open(os.path.join(relationships_path, '_deadletter.txt'), 'a+') as fp:
                fp.write(f"{str(e)}\n")
                skipped = skipped + 1
        print(f"Completed {counter}/{total_relationships} {skipped} skipped.")

    print("Completed program")
