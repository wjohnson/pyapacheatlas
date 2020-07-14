import json
import requests

from .typedef import TypeCategory
from .entity import AtlasEntity

class AtlasClient():

    def __init__(self, endpoint_url, authentication = None):
        super().__init__()
        self.authentication = authentication
        self.endpoint_url = endpoint_url
    

    def get_entity(self, guid, use_cache = False):
        results = None

        if isinstance(guid, list):
            guid_str = '&guid='.join(guid)
        else:
            guid_str = guid
        
        atlas_endpoint = self.endpoint_url + "/entity/bulk?guid={}".format(guid_str)
        getEntity = requests.get(atlas_endpoint, headers=self.authentication.get_headers())
        results = json.loads(getEntity.text)
        try:
            getEntity.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results


    def get_all_typedefs(self):
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        getTypeDefs = requests.get(atlas_endpoint, headers=self.authentication.get_headers())
        results = json.loads(getTypeDefs.text)
        try:
            getTypeDefs.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results
    

    def get_typedef(self, type_category, guid = None, name = None, use_cache = False):
        results = None
        atlas_endpoint = self.endpoint_url + "/types/{}def".format(type_category.value)

        if guid:
            atlas_endpoint = atlas_endpoint + '/guid/{}'.format(guid)
        elif name:
            atlas_endpoint = atlas_endpoint + '/name/{}'.format(name)

        getTypeDef = requests.get(atlas_endpoint, headers=self.authentication.get_headers())
        results = json.loads(getTypeDef.text)
        try:
            getTypeDef.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results
    

    def upload_typedefs(self, typedefs):
        # Should this take a list of type defs and figure out the formatting by itself?
        # Should you pass in a AtlasTypesDef object and be forced to build it yourself?
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        payload = typedefs
        required_keys = ["classificationDefs", "entityDefs", "enumDefs", "relationshipDefs", "structDefs"]
        current_keys = list(typedefs.keys())

        # Does the typedefs conform to the required pattern?
        if not any([req in current_keys for req in required_keys]):
            # Assuming this is a single typedef
            payload = {typedefs.category.lower()+"Defs":[typedefs]}
        
        postTypeDefs = requests.post(atlas_endpoint, json=payload, 
            headers=self.authentication.get_headers()
        )
        results = json.loads(postTypeDefs.text)
        try:
            postTypeDefs.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e

        return results

    @staticmethod
    def _prepare_entity_upload(batch):
        payload = batch
        required_keys = ["entities"]

        if isinstance(batch, list):
            # It's a list, so we're assuming it's a list of entities
            # TODO Incorporate AtlasEntity
            payload = {"entities":batch}
        elif isinstance(batch, dict):
            current_keys = list(batch.keys())

            # Does the dict entity conform to the required pattern?
            if not any([req in current_keys for req in required_keys]):
                # Assuming this is a single entity
                # TODO Incorporate AtlasEntity
                payload = {"entities":[batch]}
        elif isinstance(batch, AtlasEntity):
            payload = {"entities":[batch.to_json()]}
        
        return payload
    
    @staticmethod
    def validate_entities(batch):
        raise NotImplementedError


    def upload_entities(self,batch):
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/entity/bulk"

        payload = AtlasClient._prepare_entity_upload(batch)

        postBulkEntities = requests.post(atlas_endpoint, json=payload, 
            headers=self.authentication.get_headers()
        )
        results = json.loads(postBulkEntities.text)
        try:
            postBulkEntities.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e

        return results


    