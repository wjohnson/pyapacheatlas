import json
import os


def export_records(old_client, folder_path, list_of_types_to_consider):
    """
    """
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)

    for typename in list_of_types_to_consider:
        print(f"Working on {typename}")
        counter = 0
        filter_setup = {"typeName": typename}
        results = old_client.discovery.search_entities("*", search_filter=filter_setup)
        # Iterate over the search results
        # TODO: Need to implement batching since the search is now single entities
        for entity in results:
            print(f"\tWorking on batch: {counter}")
            ids_ = entity["id"]
            relevant_ids = old_client.get_entity(guid=ids_)

            with open("{}/{}-{}.json".format(folder_path, typename, counter), 'w') as fp:
                json.dump(relevant_ids.get("entities"), fp)
            
            counter = counter + 1

        print("Completed export")


def discover_guids(file_path, keys):
    """
    """
    # Now we revise the files
    if isinstance(file_path, list):
        discovered_files = file_path
    else:
        discovered_files = [os.path.join(file_path, f) for f in os.listdir(file_path)]

    known_guids = set()
    for f in discovered_files:
        dir_path, fname = os.path.split(f)
        if fname.startswith("_"):
            continue
        with open(f, 'r') as fp:
            data = json.load(fp)

        results = _recursive_guid(None, data, keys)
        known_guids = known_guids.union(results)

    return list(known_guids)


def remap_guids(guid_ref, read_path, write_path):
    """
    """
    results = []
    if not os.path.exists(write_path):
        os.mkdir(write_path)

    if isinstance(read_path, list):
        files = [os.path.abspath(f) for f in read_path]
    elif isinstance(read_path, str) and os.path.isdir(read_path):
        files = [os.path.join(read_path, f) for f in os.listdir(read_path)]
    elif isinstance(read_path, str) and os.path.isfile(read_path):
        files = [os.path.abspath(read_path)]
    else:
        raise NotImplementedError()

    # Reshape
    for f in files:
        path, file_name = os.path.split(f)
        if file_name.startswith("_"):
            continue
        print(f"Working on {f}")
        with open(f, 'r') as infp:
            data = infp.read()

        for origguid, newguid in guid_ref.items():
            data = data.replace(f'"{origguid}"', f'"{newguid}"' )
            
        with open(os.path.join(write_path, file_name), 'w') as outfp:
            outfp.write(data)
        try:
            results.extend(json.loads(data))
        except json.decoder.JSONDecodeError as e:
            print(data)
            raise e

    print("Completed remapping and writing out files")
    return results


def _recursive_guid(input_key, input_value, indicators):
    """
    """
    results = []
    if input_key in indicators:
        results.append(input_value)
        return results
    elif isinstance(input_value, list):
        for v in input_value:
            results.extend(_recursive_guid(None, v, indicators))
    elif isinstance(input_value, dict):
        for k, v in input_value.items():
            results.extend(_recursive_guid(k, v, indicators))

    return results