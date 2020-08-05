import json
import requests

from .typedef import TypeCategory
from .entity import AtlasEntity

class AtlasClient():
    """
    Provides communication between your application and the Apache Atlas
    server with your entities and type definitions.
    """

    def __init__(self, endpoint_url, authentication = None):
        """
        :param str endpoint_url: 
            The http url for communicating with your Apache Atlas server.
            It will most likely end in /api/atlas/v2.
        :param authentication:
            The method of authentication.
        :type authentication: 
            :class:`~pyapacheatlas.auth.base.AtlasAuthBase`
        """
        super().__init__()
        self.authentication = authentication
        self.endpoint_url = endpoint_url
    

    def get_entity(self, guid, use_cache = False):
        """
        Retrieve one or many guids from your Apache Atlas server.
        The use_cache parameter is currently not used but reserved for
        later use.

        :param guid: The guid or guids you want to retrieve
        :type guid: Union[str, list(str)]
        :return: A list of entities wrapped in the {"entities"} dict.
        :rtype: dict(str, list(dict))
        """
        results = None

        if isinstance(guid, list):
            guid_str = '&guid='.join(guid)
        else:
            guid_str = guid
        
        atlas_endpoint = self.endpoint_url + "/entity/bulk?guid={}".format(guid_str)
        getEntity = requests.get(atlas_endpoint, headers=self.authentication.get_authentication_headers())
        results = json.loads(getEntity.text)
        try:
            getEntity.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results


    def get_all_typedefs(self):
        """
        Retrieve all of the type defs available on the Apache Atlas server.
        
        :return: A dict containing lists of type defs wrapped in their
         corresponding definition types {"entityDefs", "relationshipDefs"}.
        :rtype: dict(str, list(dict))
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        getTypeDefs = requests.get(atlas_endpoint, headers=self.authentication.get_authentication_headers())
        results = json.loads(getTypeDefs.text)
        try:
            getTypeDefs.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results
    

    def get_typedef(self, type_category, guid = None, name = None, use_cache = False):
        """
        Retrieve a single type def based on its type category and 
        (guid or name).

        :param type_category: The type category your type def belongs to.
        :type type_category: 
            :class:`~pyapacheatlas.core.typedef.TypeCategory`
        :param str,optional guid: A valid guid. Optional if name is specified.
        :param str,optional name: A valid name. Optional if guid is specified.
        :return: The requested typedef as a dict.
        :rtype: dict
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/types/{}def".format(type_category.value)

        if guid:
            atlas_endpoint = atlas_endpoint + '/guid/{}'.format(guid)
        elif name:
            atlas_endpoint = atlas_endpoint + '/name/{}'.format(name)

        getTypeDef = requests.get(atlas_endpoint, headers=self.authentication.get_authentication_headers())
        results = json.loads(getTypeDef.text)
        try:
            getTypeDef.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e
        
        return results
    

    def upload_typedefs(self, typedefs, force_update = False):
        """
        Provides a way to upload a single or multiple type definitions.
        If you provide one type def, it will format the required wrapper
        for you based on the type category.

        If you want to upload multiple, then you'll need to create the
        wrapper yourself (e.g. {"entityDefs":[], "relationshipDefs":[]}).
        If the dict you pass in contains at least one of these Def fields
        it will be considered valid and an upload will be attempted as is.

        :param typedefs: The set of type definitions you want to upload.
        :type typedefs: dict
        :param bool force_update: 
            Whether changes should be forced (True) or whether changes
            to existing types should be discarded (False).
        :return: The results of your upload attempt from the Atlas server.
        :rtype: dict
        """
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
        
        if force_update:
            upload_typedefs_results = requests.put(atlas_endpoint, json=payload, 
                headers=self.authentication.get_authentication_headers()
            )
        else:
            upload_typedefs_results = requests.post(atlas_endpoint, json=payload, 
                headers=self.authentication.get_authentication_headers()
            )
        results = json.loads(upload_typedefs_results.text)
        try:
            upload_typedefs_results.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e

        return results

    @staticmethod
    def _prepare_entity_upload(batch):
        """
        Massages the batch to be in the right format and coerces to json/dict.
        Supports list of dicts, dict of single entity, dict of AtlasEntitiesWithExtInfo.

        :param batch: The batch of entities you want to upload.
        :type batch: Union(list(dict), dict))
        :return: Provides a dict formatted in the Atlas entity bulk upload.
        :rtype: dict(str, list(dict))
        """
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
        """
        Upload entities to your Apache Atlas server.

        :param batch: The batch of entities you want to upload.
        :type batch: Union(list(dict), dict))
        :return: The results of your bulk entity upload.
        :rtype: dict
        """
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/entity/bulk"

        payload = AtlasClient._prepare_entity_upload(batch)

        postBulkEntities = requests.post(atlas_endpoint, json=payload, 
            headers=self.authentication.get_authentication_headers()
        )
        results = json.loads(postBulkEntities.text)
        try:
            postBulkEntities.raise_for_status()
        except requests.RequestException as e:
            print(results)
            raise e

        return results


    