# This scripts provides you with the ability to extract all of the entities
# related to a given Azure Data Factory asset. It relies on the PyApacheAtlas
# and azure-identity Python packages along with the Azure CLI.

# The assumption is that you have already scanned your data estate in two
# Purview catalogs. This script helps you migrate ADF information from one
# catalog to another. The data sources must already be scanned, otherwise
# the upload of ADF copy acitvities will fail (since the inputs / outputs
# might not exist).

# You can call this script via:

# `python adf.py old-purview-name new-purview-name --factory-guid aaa-bbb-ccc-ddd-eee`

# LIMITATIONS
## Input and Output assests must already be scanned
## For contacts and experts, it must be in the same tenant

# ADF_TYPES = ["adf_pipeline", "adf_copy_activity", 
# "adf_copy_activity_run", "adf_copy_operation"]

import argparse
import copy
import json
import logging
import os

from pyapacheatlas.core import PurviewClient
from pyapacheatlas.core.util import GuidTracker

from azure.identity import AzureCliCredential

# Utility functions below, see __name__ == "__main__" for the main work
def pop_useless_fields(entity):
    """
    Remove fields that muck up an Atlas Upload from a dict.

    :param dict entity: The entity whose attributes should be changed
    :return: None
    :rtype: None
    """
    entity.pop("lastModifiedTS")
    entity.pop("status")
    entity.pop("createdBy")
    entity.pop("updatedBy")
    entity.pop("createTime")
    entity.pop("updateTime")
    entity.pop("version")
    return None


def atlas_object_id(**kwargs):
    """
    Take in either a guid or a typeName and qualifiedName
    and transform it into an approprate AtlasObjectId.

    **Kwargs**
    :param str guid: A guid string
    :param str typeName: A valid Atlas / Purview type name
    :param str qualifiedName: The qualified name of the asset this represents

    :return: A dictionary of an AtlasObjectId
    :rtype: dict
    """
    if "guid" in kwargs:
        return {"guid":kwargs["guid"]}
    elif "qualifiedName" in kwargs and "typeName" in kwargs:
        return {
                "typeName": kwargs["typeName"],
                "uniqueAttributes": {
                    "qualifiedName": kwargs["qualifiedName"]
                }
            }
    else:
        raise RuntimeError("Must specify either a guid or typeName and qualifiedName")

def cleanup_io(io_list):
    """
    For a given list of inputs or outputs attributes, remove the
    guid if typeName and uniqueAttributes are present to prevent
    a failure on upload to a different purview service.

    :param list(dict) io_list:
        A list of inputs or outputs from an Atlas Process entity.
    :return The cleaned up inputs or outputs list.
    :rtype: list(dict)
    """
    new_io = []
    for objectId in io_list:
        # If typeName and uniqueAttributes are present this
        # should be considered well formed but if it has a guid
        # we should remove it since the type and qualified name
        # is there
        if "typeName" in objectId and "uniqueAttributes" in objectId:
            if "guid" in objectId:
                objectId.pop("guid")
        new_io.append(objectId)
    return new_io

def remap_relationship(relation, GUID_MAP, client):
    """
    For a given relationship attribute, remap it to an AtlasObjectId.
    If the relationship attribute doesn't have a guid, it can't be
    looked up so it's skipped. If the type and qualified name can't
    be found in the catalog, it's skipped. Otherwise, it's returning
    an AtlasObjectId.

    :param dict relation: A relationhip attribute
    :param dict GUID_MAP: A dictionary of guids to guids used in uploads
    :param AtlasClient client: An Atlas or PurviewClient to do the lookup
    :return: Either a None or the AtlasObjectId
    :rtype: Union(None,dict)
    """
    if "guid" not in relation:
        logging.warning("Relation {} was not added for guid {} since it does not include a relationship guid".format(relationName, referred_guid))
        return None
    # Best case, this is a relationship to a guid being used
    # If that's the case, we can add the atlas object id directly
    if relation["guid"] in GUID_MAP:
        return atlas_object_id(guid=GUID_MAP[relation["guid"]])

    elif "typeName" in relation:
        # TODO: need to look it up (efficiently)
        # This is the worst case since qualified name is not
        # provided. We need to query based on the guid and get
        # the qualified name
        _exist_entity = client.get_single_entity(guid=relation["guid"],ignoreRelationships=True, minExtInfo=True)
        # Extract the qualified name so an atlas object id can be created
        try:
            _qn = _exist_entity["entity"]["attributes"]["qualifiedName"]
        except KeyError:
            logging.warning("Failed to get qualifedName for guid: {}".format(relation["guid"]))
            return None

        return atlas_object_id(typeName=relation["typeName"], qualifiedName=_qn)

    else:
        logging.info("Relation {} was not added for guid {}".format(relationName, referred_guid))
        return None

if __name__ == "__main__":
    """
    This scripts provides you with the ability to extract all of the entities
    related to a given Azure Data Factory asset. It relies on the PyApacheAtlas
    and azure-identity Python packages along with the Azure CLI.
    
    The assumption is that you have already scanned your data estate in two
    Purview catalogs. This script helps you migrate ADF information from one
    catalog to another. The data sources must already be scanned, otherwise
    the upload of ADF copy acitvities will fail (since the inputs / outputs
    might not exist).

    You can call this script via:

    `python adf.py old-purview-name new-purview-name --factory-guid aaa-bbb-ccc-ddd-eee`

    This will attempt to query the provided factory guid on the "old" Purview
    account, iterate over all of the relationships and construct and execute
    an upload against the "new" Purview account.

    Several optional parameters give you some time saving / safety measures.

    `--checkpoint file/path.json` will write out the contents of the upload
    to `file/path.json` before attempting the upload.

    `--usecheckpoint` will skip query execution if the checkpoint file exists.
    This means that --factory-guid will be ignored and the assets used for the
    upload will come from the checkpoint file. This is handy if you run into
    an Atlas Error

    `--whatif` will stop any upload and instead print the json objects to
    stdout for review.

    Data factories that are exceptionally large (>1,000 total pipelines,
    activities, runs, etc. combined) are out of scope for this script.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("old_purview_name",
        help="The name of your OLD Purview service.")
    parser.add_argument("new_purview_name",
        help="The name of your NEW Purview service.")
    parser.add_argument("--factory-guid", "-g",
        help="The guid of a data factory to start extracting metadata.")
    parser.add_argument("--checkpoint", "-c",
        help="A file path to store the results before attempting to upload.")
    parser.add_argument("--usecheckpoint", "-u", action="store_true",
        help="If the checkpoint file exists, skip attempting to query Purview.")
    parser.add_argument("--whatif", "-w", action="store_true",
        help="Do not attempt to upload, instead print what will be uploaded.")
    args = parser.parse_args()

    # Set logging
    log_level = os.environ.get("LOGLEVEL", "INFO").upper()
    logging.basicConfig(level=log_level)

    # Create an Azure CLI Credential, this can be substituted for Service
    # Principal auth using either azure.identity.EnvironmentCredential or
    # pyapacheatlas.auth.ServicePrincipalAuthentication
    cred = AzureCliCredential()

    # Set up a client to connect to the provided Purview service
    old_client = PurviewClient(
        account_name=args.old_purview_name,
        authentication=cred
    )

    # Extract out the old / existing Data Factory
    ROOT_FACTORY_GUID = args.factory_guid
    _root_resp = old_client.get_single_entity(guid=ROOT_FACTORY_GUID)
    ROOT_FACTORY_RELATIONS = _root_resp.get("referredEntities", {})
    ROOT_FACTORY = _root_resp.get("entity")

    if not ROOT_FACTORY:
        raise RuntimeError("There was no Data Factory Asset found with guid {}".format(ROOT_FACTORY_GUID))

    # If using minExtInfo = True, need to spend more time querying
    # If not, pretty much everything necessary is available in ROOT_FACTORY_RELATIONS
    gt = GuidTracker()
    GUID_MAP = {ROOT_FACTORY_GUID:gt.get_guid()}

    # Hold all of the assets that will be used in the upload
    assets_to_upload = []
    execute_queries = True

    if args.usecheckpoint:
        logging.info("Reading the checkpoint file from: {}".format(args.checkpoint))
        if not os.path.exists(args.checkpoint):
            log.info("The checkpoint file {} does not exist. Carrying on with normal execution.".format(args.checkpoint))
            execute_queries = True
        else:
            try:
                with open(args.checkpoint, 'r') as checkpoint_file:
                    assets_to_upload = json.load(checkpoint_file)
                    execute_queries = False
            except json.decoder.JSONDecodeError:
                print("The checkpoint file {} couldn't be parsed. Please check the file and verify it's non-empty and valid JSON".format(args.checkpoint))
                exit(1)
            
    if execute_queries:
        # minExtInfo == False and ignoreRelationship == False
        GUID_MAP.update( {k:gt.get_guid() for k in ROOT_FACTORY_RELATIONS.keys()} )

        for referred_guid, entity in [(ROOT_FACTORY_GUID, ROOT_FACTORY)] + list(ROOT_FACTORY_RELATIONS.items()):
            logging.info("Beginning work on {}".format(referred_guid))
            new_entity = copy.deepcopy(entity)
            referred_type = entity["typeName"]
            new_relationships = {}
            relationships = entity["relationshipAttributes"]

            # Clean up the guid to use a mapped guid for upload
            if referred_guid in GUID_MAP:
                new_entity["guid"] = GUID_MAP[referred_guid]
            else:
                _new_guid = gt.get_guid()
                GUID_MAP[referred_guid] = _new_guid
                new_entity["guid"] = _new_guid
            
            # Check if there are inputs and outputs attributes
            # They should be formed with guids
            if "inputs" in new_entity["attributes"]:
                new_inputs = cleanup_io(new_entity["attributes"]["inputs"])
                new_entity["attributes"]["inputs"] = new_inputs
                
            if "outputs" in new_entity["attributes"]:
                new_outputs = cleanup_io(new_entity["attributes"]["outputs"])
                new_entity["attributes"]["outputs"] = new_outputs

            for relationName, relation in relationships.items():
                # Relation may be either a dict or a list
                if isinstance(relation, dict):
                    new_relation = remap_relationship(relation, GUID_MAP=GUID_MAP, client=old_client)
                elif isinstance(relation, list):
                    # If it's a list, we need to iterate over each entry
                    # to do the remapping
                    new_relation = []
                    for sub_relation in relation:
                        # TODO: This could be more efficient in batching up the calls
                        # to look up the qualified names
                        new_sub_relation = remap_relationship(sub_relation, GUID_MAP=GUID_MAP, client=old_client)
                        # This could be a None, so only add when not None
                        if new_sub_relation:
                            new_relation.append(new_sub_relation)
                else:
                    logging.warning(f"The {relationName} on {referred_guid} is of an unsupported type (should be dict or list) it was {type(relation)} and skipped")
                    continue
                # With the relation remapped, add it to the dict of new relationships
                new_relationships[relationName] = new_relation

            new_entity["relationshipAttributes"] = new_relationships
            # Popping off fields that are not required and will break an upload
            pop_useless_fields(new_entity)
            assets_to_upload.append(new_entity)

    if args.whatif:
        print(json.dumps(assets_to_upload, indent=2))
        exit(0)
    if args.checkpoint:
        logging.info("Writing out the checkpoint file to: {}".format(args.checkpoint))
        with open(args.checkpoint, 'w') as checkpoint_file:
            json.dump(assets_to_upload, checkpoint_file)

    logging.info("Attempting to upload to the desired purview service.")
    new_client = PurviewClient(
        account_name=args.new_purview_name,
        authentication=cred
    )
    try:
        response = new_client.upload_entities(assets_to_upload)
        print("Succeeded uploading assets to {}".format(args.new_purview_name))
        print("Purview replied back with:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print("Failed to upload assets to {}".format(args.new_purview_name))
        print(e)
    
    # For each pipeline, get each subProcess (adf copy activities)
    # for each subProcess, get each subProcesses (copy operation) and runInstances (adf_copy_activity_run)
    # for each copy operation, get the input and output and extract
    # for each run instance, extract

# 8da59dbd-661e-4c76-b312-6d1591102cf2 : ADF > pipelines (adf_pipeline)
# e33ac285-de64-4bd0-b23d-f239a0084197 : pipeline > subProcesses (adf_copy_activity)
# 69532252-728f-4cf8-bece-319bbbffa7fe : adf_copy_activity > subProcesses (copy operations)
#                                      :                   > runInstances (adf_copy_activity_run)
# 89b13ef5-4e66-493d-bb2f-7140a73de5d8 : adf_copy_activity_run > activity (adf_copy_activity)
# 2b8428b0-f49e-4f37-83ff-692bdd5ffc91 : adf_copy_operation > in/output (actual lineage)| parent  (adf_copy_actvity)
# 45453ca5-63de-4e43-8ec1-fffd51207a5c : adf_copy_operation > in/output (actual lineage)| parent 
# 69bee4e5-ceca-49b3-9967-bbe703eaa96f : Dataset pointing to newer
# f2588b8f-161b-4c6c-b93d-612a2736a924 : Dataset pointing to older
    # res = client.get_single_entity("8da59dbd-661e-4c76-b312-6d1591102cf2", minExtInfo=True)
    # print(json.dumps(res,indent=2))
    # exit()