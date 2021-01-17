import json
from json.decoder import JSONDecodeError
import logging
import re
import requests

from .entity import AtlasClassification, AtlasEntity
from .typedef import BaseTypeDef
from .util import AtlasException, PurviewLimitation, PurviewOnly


class AtlasClient():
    """
    Provides communication between your application and the Apache Atlas
    server with your entities and type definitions.

    :param str endpoint_url:
        The http url for communicating with your Apache Atlas server.
        It will most likely end in /api/atlas/v2.
    :param authentication:
        The method of authentication.
    :type authentication:
        :class:`~pyapacheatlas.auth.base.AtlasAuthBase`
    """

    def __init__(self, endpoint_url, authentication=None):
        super().__init__()
        self.authentication = authentication
        self.endpoint_url = endpoint_url
        self.is_purview = False
        self._purview_url_pattern = r"https:\/\/[a-z0-9]*?\.(catalog\.purview.azure.com)"
        if re.match(self._purview_url_pattern, self.endpoint_url):
            self.is_purview = True

    def _handle_response(self, resp):
        """
        Safely handle an Atlas Response and return the results if valid.

        :param Response resp: The response from the request method.
        :return: A dict containing the results.
        :rtype: dict
        """

        try:
            results = json.loads(resp.text)
            resp.raise_for_status()
        except JSONDecodeError:
            raise JSONDecodeError("Error in parsing: {}".format(resp.text))
        except requests.RequestException as e:
            if "errorCode" in results:
                raise AtlasException(resp.text)
            else:
                raise e(resp.text)

        return results

    def delete_entity(self, guid):
        """
        Delete one or many guids from your Apache Atlas server.

        :param guid: The guid or guids you want to remove.
        :type guid: Union(str,list(str))
        :return:
            An EntityMutationResponse containing guidAssignments,
            mutatedEntities, and partialUpdatedEntities (list).
        :rtype: dict(str, Union(dict,list))
        """
        results = None

        if isinstance(guid, list):
            guid_str = '&guid='.join(guid)
        else:
            guid_str = guid

        atlas_endpoint = self.endpoint_url + \
            "/entity/bulk?guid={}".format(guid_str)
        deleteEntity = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers())

        results = self._handle_response(deleteEntity)

        return results

    def delete_type(self, name):
        """
        Delete a type based on the given name.

        :param str name: The name of the type you want to remove.
        :return:
            No content, should receive a 204 status code.
        :rtype: None
        """
        results = None

        atlas_endpoint = self.endpoint_url + \
            f"/types/typedef/name/{name}"
        deleteType = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers())

        try:
            deleteType.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteType.text)

        results = {"message": f"successfully delete {name}"}
        return results

    def get_entity(self, guid=None, qualifiedName=None, typeName=None):
        """
        Retrieve one or many guids from your Atlas backed Data Catalog.

        Returns a dictionary with keys "referredEntities" and "entities". You'll
        want to grab the entities values which is a list of entities.

        You can provide a single guid or a list of guids. You can provide a
        single typeName and multiple qualified names in a list.

        :param guid:
            The guid or guids you want to retrieve. Not used if using typeName
            and qualifiedName.
        :type guid: Union(str, list(str))
        :param qualifiedName:
            The qualified name of the entity you want to find. Must provide
            typeName if using qualifiedName. You may search for multiple
            qualified names under the same type. Ignored if using guid
            parameter.
        :type qualifiedName: Union(str, list(str))
        :param str typeName:
            The type name of the entity you want to find. Must provide
            qualifiedName if using typeName. Ignored if using guid parameter.
        :return:
            An AtlasEntitiesWithExtInfo object which includes a list of
            entities and accessible with the "entities" key.
        :rtype: dict(str, Union(list(dict),dict))
        """
        results = None
        parameters = {}

        if isinstance(guid, list):
            guid_str = '&guid='.join(guid)
        else:
            guid_str = guid

        qualifiedName_params = dict()
        if isinstance(qualifiedName, list):
            qualifiedName_params = {
                f"attr_{idx}:qualifiedName": qname
                for idx, qname in enumerate(qualifiedName)
            }
        else:
            qualifiedName_params = {"attr_0:qualifiedName": qualifiedName}

        if qualifiedName and typeName:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/bulk/uniqueAttribute/type/{typeName}"
            parameters.update(qualifiedName_params)

        else:
            atlas_endpoint = self.endpoint_url + \
                "/entity/bulk?guid={}".format(guid_str)

        getEntity = requests.get(
            atlas_endpoint,
            params=parameters,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getEntity)

        return results

    def get_entity_classification(self, guid, classificationName):
        """
        Retrieve a specific entity from the given entity's guid.

        :param str guid: The guid of the entity that you want to query.
        :param str classificationName: The typeName of the classification you
            want to query.
        :return: An AtlasClassification object that contains entityGuid,
            entityStatus, typeName, attributes, and propagate fields.
        :rtype: dict(str, object)
        """
        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/classification/{classificationName}"
        getClassification = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )
        results = self._handle_response(getClassification)
        return results

    def get_entity_classifications(self, guid):
        """
        Retrieve all classifications from the given entity's guid.

        :param str guid: The entity's guid.
        :return: An AtlasClassifications object that contains keys 'list' (which
            is the list of classifications on the entity), pageSize, sortBy,
            startIndex, and totalCount.
        :rtype: dict(str, object)
        """

        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/classifications"

        getClassification = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getClassification)

        return results

    def get_entity_header(self, guid=None):
        """
        Retrieve one or many entity headers from your Atlas backed Data Catalog.

        :param guid:
            The guid or guids you want to retrieve. Not used if using typeName
            and qualifiedName.
        :type guid: Union(str, list(str))
        :return:
            An AtlasEntityHeader dict which includes the keys: guid, attributes
            (which is a dict that contains qualifiedName and name keys), an
            array of classifications, and an array of glossary term headers.
        :rtype: dict
        """
        results = None
        parameters = {}

        atlas_endpoint = self.endpoint_url + \
            "/entity/guid/{}/header".format(guid)

        getEntity = requests.get(
            atlas_endpoint,
            params=parameters,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getEntity)

        return results

    def get_relationship(self, guid):
        """
        Retrieve the relationship attribute for the given guid.

        :param str guid: The unique guid for the relationship.
        :return: A dict representing AtlasRelationshipWithExtInfo with the
            relationship (what you probably care about) and referredEntities
            attributes.
        :rtype: dict(str, dict)
        """
        results = None
        atlas_endpoint = self.endpoint_url + f"/relationship/guid/{guid}"

        getResponse = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getResponse)

        return results

    def get_all_typedefs(self):
        """
        Retrieve all of the type defs available on the Apache Atlas server.

        :return:
            A dict representing an AtlasTypesDef, containing lists of
            type defs wrapped in their corresponding definition types
            {"entityDefs", "relationshipDefs"}.
        :rtype: dict(str, list(dict))
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        getTypeDefs = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getTypeDefs)

        return results

    def get_typedef(self, type_category=None, guid=None, name=None):
        """
        Retrieve a single type def based on its guid, name, or type category and
        (guid or name). Rule of thumb: Use guid if you have it, use name if you
        want to essentially use duck typing and are testing what keys you're
        reading from the response, or use type_category when you want to
        guarantee the type being returned.

        :param type_category:
            The type category your type def belongs to. You most likely want
            TypeCategory.ENTITY. Optional if name or guid is specified.
        :type type_category:
            :class:`~pyapacheatlas.core.typedef.TypeCategory`
        :param str,optional guid: A valid guid. Optional if name is specified.
        :param str,optional name: A valid name. Optional if guid is specified.
        :return: A dictionary representing an Atlas{TypeCategory}Def.
        :rtype: dict
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/types/"

        # If we are using type category
        if type_category:
            atlas_endpoint = atlas_endpoint + \
                "{}def".format(type_category.value)
        elif guid or name:
            atlas_endpoint = atlas_endpoint + "typedef"
        else:
            raise ValueError(
                "Either guid or name must be defined or type_category and one of guid or name must be defined.")

        if guid:
            atlas_endpoint = atlas_endpoint + '/guid/{}'.format(guid)
        elif name:
            atlas_endpoint = atlas_endpoint + '/name/{}'.format(name)
        else:
            raise ValueError("One of guid or name must be defined.")

        getTypeDef = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getTypeDef)

        return results

    def get_glossary(self, name="Glossary", guid=None, detailed=False):
        """
        Retrieve the specified glossary by name or guid along with the term
        headers (AtlasRelatedTermHeader: including displayText and termGuid).
        Providing the glossary name only will result in a lookup of all
        glossaries and returns the term headers (accessible via "terms" key)
        for all glossaries.
        Use detailed = True to return the full detail of terms
        (AtlasGlossaryTerm) accessible via "termInfo" key.

        :param str name:
            The name of the glossary to use, defaults to "Glossary". Not
            required if using the guid parameter.
        :param str guid:
            The unique guid of your glossary. Not required if using the
            name parameter.
        :param bool detailed:
            Set to true if you want to pull back all terms and
            not just headers.
        :return:
            The requested glossary with the term headers (AtlasGlossary) or
            with detailed terms (AtlasGlossaryExtInfo).

        :rtype: list(dict)
        """
        results = None

        if guid:
            logging.debug(f"Retreiving a Glossary based on guid: {guid}")
            atlas_endpoint = self.endpoint_url + "/glossary/{}".format(guid)
            if detailed:
                atlas_endpoint = atlas_endpoint + "/detailed"
            getResult = requests.get(
                atlas_endpoint,
                headers=self.authentication.get_authentication_headers()
            )
            results = self._handle_response(getResult)
        else:
            logging.debug(f"Retreiving a Glossary based on name: {name}")
            all_glossaries = self._get_glossaries()
            logging.debug(f"Iterating over {len(all_glossaries)} glossaries")
            for glossary in all_glossaries:
                if glossary["name"] == name:
                    logging.debug(f"Found a glossary named '{name}'")
                    if detailed:
                        logging.debug(
                            f"Recursively calling get_glossary with guid: {glossary['guid']}")
                        results = self.get_glossary(
                            guid=glossary["guid"], detailed=detailed)
                    else:
                        results = glossary
            if results is None:
                raise ValueError(
                    f"Glossary with a name of {name} was not found.")

        return results

    def _get_glossaries(self, limit=-1, offset=0, sort_order="ASC"):
        """
        Retrieve all glossaries and the term headers.

        :param int limit:
            The maximum number of glossaries to pull back.  Does not affect the
            number of term headers included in the results.
        :param int offset: The number of glossaries to skip.
        :param str sort_order: ASC for DESC sort for glossary name.
        :return: The requested glossaries with the term headers.
        :rtype: list(dict)
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/glossary"
        logging.debug("Retreiving all glossaries from catalog")

        # TODO: Implement paging with offset and limit
        getResult = requests.get(
            atlas_endpoint,
            params={"limit": limit, "offset": offset, "sort": sort_order},
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(getResult)

        return results

    def get_glossary_term(self, guid=None, name=None, glossary_name="Glossary", glossary_guid=None):
        """
        Retrieve a single glossary term based on its guid. Providing only the
        glossary_name will result in a lookup for the glossary guid. If you
        plan on looking up many terms, consider using the get_glossary method
        with the detailed argument set to True. That method will provide all
        glossary terms in a dictionary for faster lookup.

        :param str guid:
            The guid of your term. Not required if name is specified.
        :param str name:
            The name of your term's display text. Overruled if guid is
            provided.
        :param str glossary_name:
            The name of the glossary to use, defaults to "Glossary". Not
            required if using the glossary_guid parameter.
        :param str glossary_guid:
            The unique guid of your glossary. Not required if using the
            glossary_name parameter.
        :return: The requested glossary term as a dict.
        :rtype: dict
        """
        results = None

        if guid is None and name is None:
            raise ValueError("Either guid or name and glossary must be set.")

        if guid:
            atlas_endpoint = self.endpoint_url + \
                "/glossary/term/{}".format(guid)

            getTerms = requests.get(
                atlas_endpoint,
                headers=self.authentication.get_authentication_headers()
            )
            results = self._handle_response(getTerms)
        else:
            terms_in_glossary = self.get_glossary(
                name=glossary_name, guid=glossary_guid)
            for term in terms_in_glossary["terms"]:
                if term["displayText"] == name:
                    _guid = term["termGuid"]
                    results = self.get_glossary_term(guid=_guid)

        return results

    def _get_typedefs_header(self):
        """
        Get the array of AtlasTypeDefHeader that contains category, guid,
        name, and serviceType.  Massage it into a dict based on the available
        categories.

        :return: A dictionary of categories and the names of defined types.
        :rtype: dict(str, list(str))
        """
        atlas_endpoint = self.endpoint_url + "/types/typedefs/headers"
        getHeaders = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )
        results = self._handle_response(getHeaders)

        output = dict()
        for typedef in results:
            active_category = typedef["category"].lower()+"Defs"
            if active_category not in output:
                output[active_category] = []

            output[active_category].append(typedef["name"])

        return output

    @PurviewLimitation
    def classify_bulk_entities(self, entityGuids, classification):
        """
        Given a single classification, you want to apply it to many entities
        and you know their guid. This call will fail if any one of the guids
        already have the provided classification on that entity.

        :param Union(str,list) entityGuids:
            The guid or guids you want to classify.
        :param classification:
            The AtlasClassification object you want to apply to the entities.
        :type classification:
            Union(dict, :class:`~pyapacheatlas.core.entity.AtlasClassification`)
        :return: A message indicating success. The only key is 'message',
            containing a brief string.
        :rtype: dict(str,Union(list(str),str))
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/entity/bulk/classification"

        if isinstance(classification, AtlasClassification):
            classification = classification.to_json()

        classification_name = classification["typeName"]

        if isinstance(entityGuids, str):
            entityGuids = [entityGuids]
        elif isinstance(entityGuids, list):
            pass
        else:
            raise TypeError(
                "guid should be str or list, not {}".format(type(entityGuids)))

        payload = {
            # TODO: Accept AtlasClassification class
            "classification": classification,
            "entityGuids": entityGuids
        }

        postBulkClassifications = requests.post(
            atlas_endpoint,
            json=payload,
            headers=self.authentication.get_authentication_headers()
        )

        try:
            postBulkClassifications.raise_for_status()
        except requests.RequestException:
            raise AtlasException(postBulkClassifications.text)

        results = {"message": f"Successfully assigned {classification_name}",
                   "entityGuids": entityGuids
                   }
        return results

    def _classify_entity_adds(self, guid, classifications):
        """
        Update a given entity guid with the provided classifications.

        :param str guid: The guid you want to classify.
        :param list(dict) classifications:
            The list of AtlasClassification object you want to apply to the
            entity.
        :return: The name of the classification provided are returned.
        :rtype: list(str)
        """
        results = None
        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/classifications"

        postAddMultiClassifications = requests.post(
            atlas_endpoint,
            json=classifications,
            headers=self.authentication.get_authentication_headers()
        )

        try:
            postAddMultiClassifications.raise_for_status()
        except requests.RequestException:
            raise Exception(postAddMultiClassifications.text)

        results = [c["typeName"] for c in classifications]
        return results

    def _classify_entity_updates(self, guid, classifications):
        """
        Update a given entity guid with the provided classifications.

        :param str guid: The guid you want to classify.
        :param list(dict) classifications:
            The list of AtlasClassification object you want to update to the
            entity.
        :return: The name of the classification provided are returned.
        :rtype: list(str)
        """
        results = None
        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/classifications"

        putUpdateMultiClassifications = requests.put(
            atlas_endpoint,
            json=classifications,
            headers=self.authentication.get_authentication_headers()
        )

        try:
            putUpdateMultiClassifications.raise_for_status()
        except requests.RequestException:
            raise Exception(putUpdateMultiClassifications.text)

        results = [c["typeName"] for c in classifications]
        return results

    @PurviewLimitation
    def classify_entity(self, guid, classifications, force_update=False):
        """
        Given a single entity, you want to apply many classifications.
        This call will fail if any one of the classifications exist on the
        entity already, unless you choose force_update=True.

        force_update will query the existing entity and sort the classifications
        into NEW (post) and UPDATE (put) and do two requests to add and update.

        force_update is not transactional, it performs adds first. If the add
        succeeds, it moves on to the updates. If the update fails, the adds
        will continue to exist on the Atlas server and will not be rolledback.

        An error can occur if, for example, the classification has some required
        attribute that you do not provide.

        :param str guid: The guid you want to classify.
        :param classifications:
            The list of AtlasClassification object you want to apply to the
            entities.
        :type classification: 
            Union(dict, :class:`~pyapacheatlas.core.entity.AtlasClassification`)
        :param bool force_update: Mark as True if any of your classifications
            may already exist on the given entity.
        :return: A message indicating success and which classifications were
            'updates' vs 'adds' for the given guid.
        :rtype: dict(str, str)
        """
        results = None
        adds = []
        updates = []

        if isinstance(classifications, dict):
            classifications = [classifications]
        elif isinstance(classifications, AtlasClassification):
            classifications = [classifications.to_json()]
        elif isinstance(classifications, list):
            classifications = [
                c.to_json()
                if isinstance(c, AtlasClassification)
                else c for c in classifications]
        else:
            raise TypeError("classifications should be dict or list, not {}".format(
                type(classifications)))

        if force_update:
            # Get the existing entity's classifications
            existing_classifications = set([
                c["typeName"] for c in
                self.get_entity_classifications(guid=guid)["list"]
            ])

            # Sort the list into adds and updates (if exists)
            temp_adds = []
            temp_updates = []
            for classification in classifications:
                if classification["typeName"] in existing_classifications:
                    temp_updates.append(classification)
                else:
                    temp_adds.append(classification)

            # execute adds
            if len(temp_adds) > 0:
                adds = self._classify_entity_adds(guid, temp_adds)
            # execute updates
            if len(temp_updates) > 0:
                updates = self._classify_entity_updates(guid, temp_updates)
        else:
            # Assuming this is all new adds
            # execute adds
            adds = self._classify_entity_adds(guid, classifications)

        results = {
            "message": "Successfully assigned classifications",
            "guid": guid,
            "adds": adds,
            "updates": updates
        }
        return results

    def declassify_entity(self, guid, classificationName):
        """
        Given an entity guid and a classification name, remove the
        classification from the given entity.

        :param str guid: The guid for the entity that needs to be updated.
        :param str classificationName:
            The name of the classification to be deleted.
        :return: A success message repeating what was deleted. The only key
            is 'message', containing the classification name and guid.
        :rtype: dict(str, str)
        """
        results = None
        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/classification/{classificationName}"

        deleteEntityClassification = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers()
        )

        try:
            deleteEntityClassification.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteEntityClassification.text)

        results = {"message":
                   f"Successfully removed classification: {classificationName} from {guid}.",
                   "guid": guid,
                   }
        return results
    
    @staticmethod
    def _prepare_type_upload(typedefs = None, **kwargs):
        """
        Massage the type upload. See rules in upload_typedefs.
        """
        payload = {}
        required_keys = ["classificationDefs", "entityDefs",
                         "enumDefs", "relationshipDefs", "structDefs"]

        # If typedefs is defined as a dict and it contains at least one of the
        # required keys for the TypeREST definition.
        if isinstance(typedefs,dict) and len(set(typedefs.keys()).intersection(required_keys)) > 0:
            payload = typedefs
        # It isn't in the standard form but is it defined?
        elif typedefs is not None:
            # Assuming this is a single typedef
            key = None
            if isinstance(typedefs, BaseTypeDef):
                key = typedefs.category.lower() + "Defs"
                val = [typedefs.to_json()]
            elif isinstance(typedefs, dict):
                key = typedefs["category"].lower() + "Defs"
                val = [typedefs]
            else:
                raise NotImplementedError(
                    "Uploading an object of type '{}' is not supported."
                    .format(type(typedefs))
                )
            payload = {key: val}
        # Did we set any of the xDefs as arguments?
        elif len( set(kwargs.keys()).intersection(required_keys) ) > 0:
            for typeRestKey in required_keys:
                # Did we specify this key?
                if typeRestKey in kwargs.keys():
                    payload[typeRestKey] = [
                        t.to_json() if isinstance(t, BaseTypeDef) else t
                        for t in kwargs[typeRestKey]
                    ]
        else:
            raise RuntimeError(
                f"Failed to upload typedefs for arguments: {kwargs}"
            )
        return payload

    def upload_typedefs(self, typedefs = None, force_update=False, **kwargs):
        """
        Provides a way to upload a single or multiple type definitions.
        If you provide one type def, it will format the required wrapper
        for you based on the type category.

        If you want to upload multiple type defs or typedefs of different
        category, you can pass the in kwargs `entityDefs`, `classificationDefs`,
        `enumDefs`, `relationshipDefs`, `structDefs` which take in a list of
        dicts or appropriate TypeDef objects.
        
        Otherwise, you can pass in the wrapper yourself (e.g. {"entityDefs":[],
        "relationshipDefs":[]}) by providing that dict to the typedefs
        parameter. If the dict you pass in contains at least one of these Def
        fields it will be considered valid and an upload will be attempted.

        typedefs also takes in a BaseTypeDef object or a valid AtlasTypeDef
        json / dict. If you provide a value in typedefs, it will ignore the
        kwargs parameters.

        When using force_update, it will look up all existing types and see
        if any of your provided types exist.  If they do exist, they will be
        updated. If they do not exist, they will be issued as new. New types
        are uploaded first. Existing types are updated second. There are no
        transactional updates.  New types can succeed and be inserted while
        a batch of existing types can fail and not be updated.

        :param typedefs: The set of type definitions you want to upload.
        :type typedefs: Union(dict, :class:`~pyapacheatlas.core.typedef.BaseTypeDef`)
        :param bool force_update:
            Set to True if your typedefs contains any existing entities.
        :return: The results of your upload attempt from the Atlas server.
            :rtype: dict
        
        Kwargs:
            :param entityDefs: EntityDefs to upload.
            :type entityDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param classificationDefs: classificationDefs to upload.
            :type classificationDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param enumDefs: enumDefs to upload.
            :type enumDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param relationshipDefs: relationshipDefs to upload.
            :type relationshipDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param structDefs: structDefs to upload.
            :type structDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))

        Returns:
            
        """
        # Should this take a list of type defs and figure out the formatting
        # by itself?
        # Should you pass in a AtlasTypesDef object and be forced to build
        # it yourself?
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        payload = AtlasClient._prepare_type_upload(typedefs, **kwargs)

        if not force_update:
            # This is just a plain push of new entities
            upload_typedefs_results = requests.post(
                atlas_endpoint, json=payload,
                headers=self.authentication.get_authentication_headers()
            )
            results = self._handle_response(upload_typedefs_results)
        else:
            # Look up all entities by their header
            types_from_client = self._get_typedefs_header()
            existing_types = dict()
            new_types = dict()

            # Loop over the intended upload and see if they exist already
            # If they do not exist, shuffle them to the new_types upload.
            # if they do exist, shuffle to the existing types upload.
            for cat, typelist in payload.items():
                existing_types[cat] = []
                new_types[cat] = []
                for t in typelist:
                    if t["name"] in types_from_client[cat]:
                        existing_types[cat].append(t)
                    else:
                        new_types[cat].append(t)

            upload_new = requests.post(
                atlas_endpoint, json=new_types,
                headers=self.authentication.get_authentication_headers()
            )
            results_new = self._handle_response(upload_new)

            upload_exist = requests.put(
                atlas_endpoint, json=existing_types,
                headers=self.authentication.get_authentication_headers()
            )
            results_exist = self._handle_response(upload_exist)

            # Merge the results
            results = results_new
            for cat, updatedtypelist in results_exist.items():
                if cat not in results:
                    results[cat] = []
                results[cat].extend(updatedtypelist)

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
            # Handles any type of AtlasEntity and mixed batches of dicts
            # and AtlasEntities
            dict_batch = [e.to_json() if isinstance(e, AtlasEntity) else e for e in batch]
            payload = {"entities": dict_batch}
        elif isinstance(batch, dict):
            current_keys = list(batch.keys())

            # Does the dict entity conform to the required pattern?
            if not any([req in current_keys for req in required_keys]):
                # Assuming this is a single entity
                # DESIGN DECISION: I'm assuming, if you're passing in
                # json, you know the schema and I will not support
                # AtlasEntity here.
                payload = {"entities": [batch]}
        elif isinstance(batch, AtlasEntity):
            payload = {"entities": [batch.to_json()]}
        else:
            raise NotImplementedError(f"Uploading type: {type(batch)} is not supported.")

        return payload

    def upload_entities(self, batch):
        """
        Upload entities to your Atlas backed Data Catalog.

        :param batch:
            The batch of entities you want to upload. Supports a single dict,
            AtlasEntity, list of dicts, list of atlas entities.
        :type batch:
            Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`,
            list(dict), list(:class:`~pyapacheatlas.core.entity.AtlasEntity`) )
        :return: The results of your bulk entity upload.
        :rtype: dict
        """
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/entity/bulk"

        payload = AtlasClient._prepare_entity_upload(batch)

        postBulkEntities = requests.post(
            atlas_endpoint,
            json=payload,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(postBulkEntities)

        return results

    def upload_relationship(self, relationship):
        """
        Upload a AtlasRelationship json. Should take the form of the following::

            {
                "typeName": "hive_table_columns",
                "attributes": {},
                "guid": -100,
                "end1": {
                    "guid": assignments["-1"]
                },
                "end2": {
                    "guid": assignments["-5"]
                    }
            }

        :param dict relationship: The relationship you want to upload.
        :return: The results of your relationship upload.
        :rtype: dict
        """
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/relationship"

        # TODO: Handling Updates instead of just creates
        relationshipResp = requests.post(
            atlas_endpoint,
            json=relationship,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(relationshipResp)

        return results

    def upload_terms(self, batch, force_update=False):
        """
        Upload terms to your Atlas backed Data Catalog.

        :param batch: A list of AtlasGlossaryTerm objects to be uploaded.
        :type batch: list(dict)
        :return:
            A list of AtlasGlossaryTerm objects that are the results from
            your upload.
        :rtype: list(dict)
        """
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/glossary/terms"

        postResp = requests.post(
            atlas_endpoint,
            json=batch,
            headers=self.authentication.get_authentication_headers()
        )

        results = self._handle_response(postResp)

        return results

    def _search_generator(self, search_params):
        """
        Generator to page through the search query results.
        """
        atlas_endpoint = self.endpoint_url + "/search/advanced"
        offset = 0

        while True:
            postSearchResults = requests.post(
                atlas_endpoint,
                json=search_params,
                headers=self.authentication.get_authentication_headers()
            )
            results = self._handle_response(postSearchResults)
            return_values = results["value"]
            return_count = len(return_values)

            if return_count == 0:
                return

            offset = offset + return_count
            search_params["offset"] = offset
            try:
                yield return_values
            except StopIteration:
                return

    @PurviewOnly
    def search_entities(self, query, limit=50, search_filter=None):
        """
        Search entities based on a query and automaticall handles limits and
        offsets to page through results.

        The limit provides how many records are returned in each batch with a
        maximum of 1,000 entries per page.

        :param str query: The search query to be executed.
        :param int limit:
            A non-zero integer representing how many entities to
            return for each page of the search results.
        :param dict search_filter: A search filter to reduce your results.
        :return: The results of your search as a generator.
        :rtype: Iterator(list(dict))
        """

        if limit > 1000 or limit < 1:
            raise ValueError(
                "The limit parameter must be non-zero and less than 1,000."
            )

        search_params = {
            "keywords": query,
            "limit": limit,
            "offset": 0
        }
        # TODO: Make this smarter, make it easier to create filters
        # without having to know how to make a filter object.
        if search_filter:
            # Example search filter might look like:
            # {"filter": {"typeName": "DataSet", "includeSubTypes": True} }
            search_params.update({"filter": search_filter})

        search_generator = self._search_generator(search_params)

        return search_generator


class PurviewClient(AtlasClient):
    """
    Provides communication between your application and the Azure Purview
    service. Simplifies the requirements for knowing the endpoint url and
    requires only the Purview account name.

    :param str account_name:
        Your Purview account name.
    :param authentication:
        The method of authentication.
    :type authentication:
        :class:`~pyapacheatlas.auth.base.AtlasAuthBase`
    """

    def __init__(self, account_name, authentication=None):
        endpoint_url = f"https://{account_name.lower()}.catalog.purview.azure.com/api/atlas/v2"
        super().__init__(endpoint_url, authentication)
