from migrate_util import discover_guids, remap_guids, _recursive_guid
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core import AtlasClient
from pyapacheatlas.auth import ServicePrincipalAuthentication
import argparse
import configparser
import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
config = configparser.ConfigParser()
config.read("./samples/migratePurview/config.ini")


folder_path = config["Default"]["GlossaryFolder"]
output_path = config["Default"]["GlossaryRemapped"]

unchanged_path = os.path.join(folder_path, "glossary.json")
glossary_prep_path = os.path.join(output_path, "glossary_prepared.json")

relationships_guid_path = config["Default"]["GlossaryRelationships"]
old_to_new_glossary_guid_path = config["Default"]["GlossaryOldToNew"]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-download", action="store_true",
                        help="Use if you've already written the glossary to disk.")
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

    gt = GuidTracker()

    # Export the glossary terms
    if not args.skip_download:
        print("Exporting the old glossary terms")
        glossary_terms = old_client.glossary.get_glossary(detailed=True)
        glossary_terms_copy = list(glossary_terms["termInfo"].values())
        with open(unchanged_path, 'w') as fp:
            json.dump(glossary_terms_copy, fp)

    else:
        print("Loading existing glossary terms from disk")
        with open(unchanged_path, 'r') as fp:
            glossary_terms_copy = json.load(fp)

    # Discover the Relationship Guids that will be uploaded later
    relationship_guids = _recursive_guid(None, glossary_terms_copy, [
                                         "relationGuid", "relationshipGuid"])
    with open(relationships_guid_path, 'w') as fp:
        for relationship in relationship_guids:
            fp.write(relationship)
            fp.write("\n")

    # Remove the other attributes that interfere with upload
    # including the relationship attributes
    print("Getting the new glossary id")
    new_glossary = new_client.glossary.get_glossary("Glossary")
    new_glossary_guid = new_glossary["guid"]
    print(f"The new glossary guid is: {new_glossary_guid}")

    print("Writing glossary terms in prep to be re-mapped to temporary guids")
    with open(glossary_prep_path, 'w') as fp:
        json.dump(glossary_terms_copy, fp)

    print("Discovering guids and remapping guids")
    # Remap the guids and write them back out to the output_path
    old_glossary_guids = discover_guids(
        [glossary_prep_path], ["guid", "termGuid"])
    # Provide a new guid (temp guid) for the upload (must be a negative number)
    orig_guid_to_temp_guid = {g: str(gt.get_guid())
                              for g in old_glossary_guids}
    # Execute the find and replace of old guid with temp guid
    remapped_glossary = remap_guids(orig_guid_to_temp_guid, [
                                    glossary_prep_path], output_path)
    
    print("Processing the glossary terms in memory")
    headers = ["antonyms", "classifies", "isA", "preferredTerms",
               "preferredToTerms", "replacedBy", "replacementTerms",
               "seeAlso", "synonyms", "translatedTerms", "translationTerms",
               "validValues", "validValuesFor"
               ]
    
    for term in remapped_glossary:
        # Remove everything that will be created automatically
        try:
            term["anchor"].pop("relationGuid")
            term.pop("lastModifiedTS")
            term.pop("createdBy")
            term.pop("qualifiedName")
            term.pop("updatedBy")
            term.pop("createTime")
            term.pop("updateTime")
            term["assignedEntities"] = []
            # LIMITATION: Does not support Term Templates at this time
            term["attributes"] = {}
            term["anchor"].update({"glossaryGuid":new_glossary_guid})
            # Remove the associated terms as they will be added back with relationShips
            for header in headers:
                if header in term:
                    term.pop(header)
        except KeyError as e:
            print(term)
            raise e

    # Get a mapping from the original guid to the name
    # To be used in mapping the original guid to the new catalog's guids.
    # (orig) to (temp) to (name) to (new)
    temp_guid_to_name = {g["guid"]: g["name"] for g in remapped_glossary}

    input("About to upload remapped glossary terms to the new catalog. Continue? Ctrl + C to back out")
    # Upload the guids
    results = new_client.glossary.upload_terms(batch=remapped_glossary)
    # Get the second half of the mapping (B to C)
    term_name_to_new_guid = {g["name"]: g["guid"] for g in results}

    # Create the (orig) to (temp) to (name) to (new) mapping
    old_guid_to_new_guid = dict()
    for orig_guid, temp_guid in orig_guid_to_temp_guid.items():
        if temp_guid in temp_guid_to_name:
            term_name = temp_guid_to_name[temp_guid]
            if term_name in term_name_to_new_guid:
                new_guid = term_name_to_new_guid[term_name]
                old_guid_to_new_guid[orig_guid] = new_guid

    with open(old_to_new_glossary_guid_path, 'w') as fp:
        json.dump(old_guid_to_new_guid, fp)

    print("Completed glossary upload and provided REMAP_GLOSSARY.json")
