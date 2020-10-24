import json
from json.decoder import JSONDecodeError
import logging
import requests

from .entity import AtlasEntity
from .typedef import BaseTypeDef


class AtlasClient():
    """
    Provides communication between your application and the Apache Atlas
    server with your entities and type definitions.
    """

    def __init__(self, endpoint_url, authentication=None):
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

    def _handle_response(self, resp):
        """
        Safely handle an Atlas Response and return the results if valid.

        :param Response resp: The response from the request method.
        :return: A dict containing the results.
        :rtype: dict
        """

        try:
            resp.raise_for_status()
            results = json.loads(resp.text)
        except requests.RequestException:
            raise Exception(resp.text)
        except JSONDecodeError:
            raise Exception("Error in parsing: {}".format(resp.text))
        return results

    def delete_entity(self, guid):
        """
        Delete one or many guids from your Apache Atlas server.

        :param guid: The guid or guids you want to remove.
        :type guid: Union[str, list(str)]
        :return:
            An EntityMutationResponse containing guidAssignments,
            mutatedEntities, and partialUpdatedEntities (list).
        :rtype: dict(str, Union[dict,list])
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

    def get_entity(self, guid = None, qualifiedName = None, typeName = None):
        """
        Retrieve one or many guids from your Atlas backed Data Catalog.

        :param guid:
            The guid or guids you want to retrieve. Not used if using typeName
            and qualifiedName.
        :type guid: Union[str, list(str)]
        :param qualifiedName:
            The qualified name of the entity you want to find. Must provide
            typeName if using qualifiedName. You may search for multiple
            qualified names under the same type. Ignored if using guid
            parameter.
        :type qualifiedName: Union[str, list(str)]
        :param str typeName:
            The type name of the entity you want to find. Must provide
            qualifiedName if using typeName. Ignored if using guid parameter.
        :return:
            An AtlasEntitiesWithExtInfo object which includes a list of
            entities and accessible with the "entities" key.
        :rtype: dict(str, Union[list(dict),dict])
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
                f"attr_{idx}:qualifiedName":qname 
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
            params= parameters,
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

        :return: A dict representing an AtlasTypesDef, containing lists of
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

    def get_typedef(self, type_category, guid=None, name=None):
        """
        Retrieve a single type def based on its type category and
        (guid or name).

        :param type_category:
            The type category your type def belongs to. You most likely want
            TypeCategory.ENTITY.
        :type type_category:
            :class:`~pyapacheatlas.core.typedef.TypeCategory`
        :param str,optional guid: A valid guid. Optional if name is specified.
        :param str,optional name: A valid name. Optional if guid is specified.
        :return: A dictionary representing an Atlas{TypeCategory}Def.
        :rtype: dict
        """
        results = None
        atlas_endpoint = self.endpoint_url + \
            "/types/{}def".format(type_category.value)

        if guid:
            atlas_endpoint = atlas_endpoint + '/guid/{}'.format(guid)
        elif name:
            atlas_endpoint = atlas_endpoint + '/name/{}'.format(name)

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

    def upload_typedefs(self, typedefs, force_update=False):
        """
        Provides a way to upload a single or multiple type definitions.
        If you provide one type def, it will format the required wrapper
        for you based on the type category.

        If you want to upload multiple, then you'll need to create the
        wrapper yourself (e.g. {"entityDefs":[], "relationshipDefs":[]}).
        If the dict you pass in contains at least one of these Def fields
        it will be considered valid and an upload will be attempted as is.

        When using force_update, it will look up all existing types and see
        if any of your provided types exist.  If they do exist, they will be
        updated. If they do not exist, they will be issued as new. New types
        are uploaded first. Existing types are updated second. There are no
        transactional updates.  New types can succeed and be inserted while
        a batch of existing types can fail and not be updated.

        :param typedefs: The set of type definitions you want to upload.
        :type typedefs: dict
        :param bool force_update:
            Set to True if your typedefs contains any existing entities.
        :return: The results of your upload attempt from the Atlas server.
        :rtype: dict
        """
        # Should this take a list of type defs and figure out the formatting
        # by itself?
        # Should you pass in a AtlasTypesDef object and be forced to build
        # it yourself?
        results = None
        atlas_endpoint = self.endpoint_url + "/types/typedefs"

        payload = typedefs
        required_keys = ["classificationDefs", "entityDefs",
                         "enumDefs", "relationshipDefs", "structDefs"]
        current_keys = list(typedefs.keys())

        # Does the typedefs conform to the required pattern?
        if not any([req in current_keys for req in required_keys]):
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
            # TODO Incorporate AtlasEntity
            payload = {"entities": batch}
        elif isinstance(batch, dict):
            current_keys = list(batch.keys())

            # Does the dict entity conform to the required pattern?
            if not any([req in current_keys for req in required_keys]):
                # Assuming this is a single entity
                # TODO Incorporate AtlasEntity
                payload = {"entities": [batch]}
        elif isinstance(batch, AtlasEntity):
            payload = {"entities": [batch.to_json()]}

        return payload

    def upload_entities(self, batch):
        """
        Upload entities to your Atlas backed Data Catalog.

        :param batch: The batch of entities you want to upload.
        :type batch: Union(list(dict), dict))
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
        Upload a relationship json.

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
                raise StopIteration

            offset = offset + return_count
            search_params["offset"] = offset
            yield return_values

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
        :rtype: Iterator[list(dict)]
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
            # "filter": {"add": [{"typeName": "misc_table",
            # "includeSubTypes": True}]}
            search_params.update({"filter": search_filter})

        search_generator = self._search_generator(search_params)

        return search_generator
