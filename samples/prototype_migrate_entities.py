import argparse
import os

from pyapacheatlas.readers import ExcelConfiguration, ExcelReader
from pyapacheatlas.core import (
    AtlasAttributeDef, AtlasClient, AtlasEntity,
    EntityTypeDef, TypeCategory
)
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.auth import ServicePrincipalAuthentication
import json
tenant_id = ""
client_id = ""
client_secret = ""
data_catalog_name = ""

atlas_endpoint = "https://" + data_catalog_name + \
    ".catalog.babylon.azure.com/api/atlas/v2"

def export_records(folder_path, list_of_types_to_consider):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    for typename in list_of_types_to_consider:
        print(f"Working on {typename}")
        counter = 0
        filter_setup = {"typeName": typename}
        results = atlas_client.search_entities("*", search_filter=filter_setup)
        # Iterate over the search results
        for batch in results:
            print(f"Working on batch: {counter}")
            ids_ = [r["id"] for r in batch]
            if len(ids_) > 0:
                relevant_ids = atlas_client.get_entity(guid=ids_)

                with open("{}/{}-{}.json".format(folder_path, typename, counter), 'w') as fp:
                    json.dump( relevant_ids.get("entities"), fp)
            counter = counter + 1

        print("Completed export")

def recurse_guid(obj, guid_tracker):
    results = []
    guid_names = [
        "guid", "entityGuid", "relationshipGuid", "termGuid",
    ]
    print(obj)
    if isinstance(obj, list):
        for i in obj:
            results.extend( recurse_guid(i, guid_tracker))
    elif isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v, list):
                for i in v:
                    results.extend( recurse_guid(i, guid_tracker) )
            elif isinstance(v, dict):
                results.extend(recurse_guid(v, guid_tracker))
            elif k in guid_names:
                results.append((v, guid_tracker.get_guid()))
    return results

def extract_guid_from_dict(d):
    guid_names = [
        "guid", "entityGuid", "relationshipGuid", "termGuid",
    ]
    guids = [v for k,v in d.items() if k in guid_names]
    return guids



def discover_guids(file_path):
    # Now we revise the files
    gt = GuidTracker()

    discovered_files = os.listdir(file_path)

    guid_references = dict()
    for f in discovered_files:
        with open(os.path.join(folder_path, f), 'r') as fp:
            data = json.load(fp)
        
        for row in data:
            guid_references[row["guid"]] = []
            # Traverse the relationship attributes
            # They are either dictionaries (best case) or lists of dicts.
            for relationship in row["relationshipAttributes"].values():
                if isinstance(relationship, dict):
                    guid_references[row["guid"]].extend(
                        extract_guid_from_dict(relationship)
                    )
                else:
                    # Assuming this is a list
                    for elem in relationship:
                        if not isinstance(elem, list):
                            print(row)
                        guid_references[row["guid"]].extend(
                            extract_guid_from_dict(elem)
                        )
                    
    return guid_references
        
    
def remap_guids(guid_ref, file_path, guid_start = -1000):
    gt = GuidTracker(starting=guid_start)
    new_folder_path = file_path + "remap"
    if not os.path.exists(new_folder_path):
        os.mkdir(new_folder_path)
    
    mapping = dict()
    for k, v in guid_ref.items():
        if k not in mapping:
            mapping[k] = gt.get_guid()
        
        for elem in v:
            if elem not in mapping:
                mapping[elem] = gt.get_guid()
    
    for f in os.listdir(file_path):
        with open(os.path.join(file_path, f), 'r') as infp:
            data = infp.read()
        for origguid, newguid in mapping.items():
            data = data.replace(origguid, str(newguid))
        with open(os.path.join(new_folder_path, f), 'w') as outfp:
            outfp.write(data)
            
    return mapping


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-query", action="store_true", help="Whether you should skip querying.")
    args = parser.parse_args()

    auth = ServicePrincipalAuthentication(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    atlas_client = AtlasClient(
        endpoint_url=atlas_endpoint,
        authentication=auth
    )

    folder_path = "./mydata"
    # Get all the types you want to "export"
    list_of_types_to_consider = ["demo_column", "demo_table"]

    if not args.no_query:
        export_records(folder_path, list_of_types_to_consider)

    guid_refs = discover_guids(folder_path)

    remap_guids(guid_refs, folder_path)

    # TODO: How do you find the right order to upload these entities?

