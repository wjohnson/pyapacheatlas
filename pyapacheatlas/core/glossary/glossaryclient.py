import logging
import json
import warnings

import requests

from ..entity import AtlasEntity
from ..util import AtlasBaseClient, AtlasException
from .term import _CrossPlatformTerm


class GlossaryClient(AtlasBaseClient):
    def __init__(self, endpoint_url, authentication, **kwargs):
        self.endpoint_url = endpoint_url
        self.authentication = authentication
        super().__init__(**kwargs)

    # Glossary
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(getResult)

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
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
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

    # Terms section
    def get_term(self, guid=None, name=None, glossary_name="Glossary", glossary_guid=None):
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
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )
            results = self._handle_response(getTerms)
        else:
            terms_in_glossary = self.get_glossary(
                name=glossary_name, guid=glossary_guid)
            for term in terms_in_glossary["terms"]:
                if term["displayText"] == name:
                    _guid = term["termGuid"]
                    results = self.get_term(guid=_guid)

        return results

    def upload_term(self, term, force_update=False, **kwargs):
        """
        Upload a single term to Apache Atlas.

        Provide an AtlasGlossaryTerm or dictionary.

        :param term: The term to be uploaded.
        :type term: Union(:class:`~pyapacheatlas.core.glossary.term.AtlasGlossaryTerm`, dict)
        :param bool force_update: Currently not used.

        Kwargs:
            :param dict parameters: The parameters to pass into the url.

        :return: The uploaded term's current state.
        :rtype: dict        
        """
        payload = {}
        atlas_endpoint = self.endpoint_url + "/glossary/term"

        if isinstance(term, dict):
            payload = term
        elif isinstance(term, _CrossPlatformTerm):
            payload = term.to_json()
        else:
            raise TypeError(
                f"The type {type(term)} is not supported. Please use a dict, AtlasGlossaryTerm, or PurviewGlossaryTerm")

        postResp = requests.post(
            atlas_endpoint,
            json=payload,
            params=kwargs.get("parameters", {}),
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResp)

        return results

    def upload_terms(self, terms, force_update=False, **kwargs):
        """
        Upload a multiple terms to Apache Atlas.

        Provide a list of AtlasGlossaryTerms or dictionaries.

        :param terms: The terms to be uploaded.
        :type terms: list(Union(:class:`~pyapacheatlas.core.glossary.term.PurviewGlossaryTerm`, :class:`~pyapacheatlas.core.glossary.term.AtlasGlossaryTerm`, dict))
        :param bool force_update: Currently not used.

        Kwargs:
            :param dict parameters: The parameters to pass into the url.

        :return: The uploaded term's current state.
        :rtype: dict        
        """
        results = None
        atlas_endpoint = self.endpoint_url + "/glossary/terms"
        payload = [t.to_json() if isinstance(
            t, _CrossPlatformTerm) else t for t in terms]

        postResp = requests.post(
            atlas_endpoint,
            json=payload,
            params=kwargs.get("parameters", {}),
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResp)

        return results

    # assignTerm section
    def get_termAssignedEntities(self, termGuid=None, termName=None, glossary_name="Glossary", limit=-1, offset=0, sort="ASC", glossary_guid=None):
        """
        Page through the assigned entities for the given term.

        :param str termGuid: The guid for the term. Ignored if using termName.
        :param str termName: The name of the term. Optional if using termGuid.
        :param str glossary_name:
            The name of the glossary. Defaults to Glossary. Ignored if using termGuid.

        :return: A list of Atlas relationships between the given term and entities.
        :rtype: list(dict)
        """
        results = None

        if termName:
            _discoveredTerm = self.get_term(
                name=termName, glossary_name=glossary_name,
                glossary_guid=glossary_guid)
            termGuid = _discoveredTerm["guid"]

        atlas_endpoint = self.endpoint_url + \
            f"/glossary/terms/{termGuid}/assignedEntities"

        # TODO: Implement paging with a generator
        getAssignments = requests.get(
            atlas_endpoint,
            params={"limit": limit, "offset": offset, "sort": sort},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(getAssignments)
        return results

    def assignTerm(self, entities, termGuid=None, termName=None, glossary_name="Glossary", glossary_guid=None):
        """
        Assign a single term to many entities. Provide either a term guid
        (if you know it) or provide the term name and glossary name. If
        term name is provided, term guid is ignored.

        As for entities, you may provide a list of
        :class:`~pyapacheatlas.core.entity.AtlasEntity` BUT they must have a
        valid guid defined (not None, not -N) or it will fail with a transient
        error. Alternatively, you may provide your own dict that contains a
        'guid' key and value.

        :param entities: The list of entities that should have the term assigned.
        :type entities: list(Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`))
        :param str termGuid: The guid for the term. Ignored if using termName.
        :param str termName: The name of the term. Optional if using termGuid.
        :param str glossary_name:
            The name of the glossary. Defaults to Glossary. Ignored if using termGuid.

        :return: A dictionary indicating success or failure.
        :rtype: dict
        """
        results = None

        # Massage the data into dicts
        # Assumes the AtlasEntity does not have guid defined
        json_entities = []
        for e in entities:
            if isinstance(e, AtlasEntity) and e.guid != None:
                json_entities.append({"guid": e.guid})
            elif isinstance(e, dict) and "guid" in e:
                json_entities.append({"guid": e["guid"]})
            else:
                warnings.warn(
                    f"{str(e)} does not contain a guid and will be skipped.",
                    category=UserWarning, stacklevel=2)

        if len(json_entities) == 0:
            raise RuntimeError(
                "No Atlas Entities or Dictionaries with Guid were provided.")

        # Term Name will supercede term guid.
        if termName:
            _discoveredTerm = self.get_term(
                name=termName, glossary_name=glossary_name,
                glossary_guid=glossary_guid
                )
            termGuid = _discoveredTerm["guid"]

        atlas_endpoint = self.endpoint_url + \
            f"/glossary/terms/{termGuid}/assignedEntities"

        postAssignment = requests.post(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers(),
            json=json_entities,
            **self._requests_args
        )

        try:
            postAssignment.raise_for_status()
        except requests.RequestException:
            raise Exception(postAssignment.text)

        results = {"message": f"Successfully assigned term to entities."}
        return results

    def delete_assignedTerm(self, entities, termGuid=None, termName=None, glossary_name="Glossary", glossary_guid=None):
        """
        Remove a single term from many entities. Provide either a term guid
        (if you know it) or provide the term name and glossary name. If
        term name is provided, term guid is ignored.

        As for entities, you may provide a list of
        :class:`~pyapacheatlas.core.entity.AtlasEntity` BUT they must have a
        valid guid defined (not None, not -N) and a relationshipAttribute of
        **meanings** with an entry that has the term's guid and relationshipGuid.
        Alternatively, you may provide your own dict that contains a
        'guid' and 'relationshipGuid' key and value. Lastly, you may also pass in the
        results of the 'entities' key from the `get_entity` method and it
        will parse the relationshipAttributes properly and silently ignore the
        meanings that do not match the termGuid.

        :param entities: The list of entities that should have the term assigned.
        :type entities: list(Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`))
        :param str termGuid: The guid for the term. Ignored if using termName.
        :param str termName: The name of the term. Optional if using termGuid.
        :param str glossary_name:
            The name of the glossary. Defaults to Glossary. Ignored if using termGuid.

        :return: A dictionary indicating success or failure.
        :rtype: dict
        """
        results = None

        # Need the term guid to build the payload
        if termName:
            _discoveredTerm = self.get_term(
                name=termName, glossary_name=glossary_name,
                glossary_guid=glossary_guid)
            termGuid = _discoveredTerm["guid"]

        # Massage the data into dicts
        # Assumes the AtlasEntity does not have guid defined
        json_entities = []
        for e in entities:
            # Support AtlasEntity
            if isinstance(e, AtlasEntity) and e.guid != None:
                if "meanings" in e.relationshipAttributes:
                    _temp_payload = [
                        {"guid": e.guid,
                            "relationshipGuid": ra["relationshipGuid"]}
                        for ra in e.relationshipAttributes.get("meanings", [])
                        if ra.get("guid", "") == termGuid
                    ]
                    json_entities.extend(_temp_payload)
            # Support response from Atlas parsing
            elif isinstance(e, dict) and "guid" in e and "relationshipAttributes" in e:
                _temp_payload = [
                    {"guid": e["guid"],
                        "relationshipGuid": ra["relationshipGuid"]}
                    for ra in e["relationshipAttributes"].get("meanings", [])
                    if ra.get("guid", "") == termGuid
                ]
                json_entities.extend(_temp_payload)
            # Support arbitrary dictionary
            elif isinstance(e, dict) and "guid" in e and "relationshipGuid" in e:
                json_entities.append(
                    {"guid": e["guid"], "relationshipGuid": e["relationshipGuid"]})
            else:
                warnings.warn(
                    f"{str(e)} does not contain a guid or relationshipGuid and will be skipped.",
                    category=UserWarning, stacklevel=2)

        if len(json_entities) == 0:
            raise RuntimeError(
                "No Atlas Entities or Dictionaries with Guid were provided.")

        atlas_endpoint = self.endpoint_url + \
            f"/glossary/terms/{termGuid}/assignedEntities"

        deleteAssignment = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers(),
            json=json_entities,
            **self._requests_args
        )

        try:
            deleteAssignment.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteAssignment.text)

        results = {
            "message": f"Successfully deleted assigned term from entities."}
        return results


class PurviewGlossaryClient(GlossaryClient):

    def __init__(self, endpoint_url, authentication, **kwargs):
        super().__init__(endpoint_url, authentication, **kwargs)

    # Terms section
    def upload_term(self, term, includeTermHierarchy=True, force_update=False, **kwargs):
        """
        Upload a single term to Azure Purview. If you plan on uploading many
        terms programmatically, you might look at
        `PurviewClient.glossary.upload_terms` or 
        `PurviewClient.glossary.import_terms`.

        Provide a PurviewGlossaryTerm or dictionary.

        :param term: The term to be uploaded.
        :type term: Union(:class:`~pyapacheatlas.core.glossary.term.PurviewGlossaryTerm`, dict)
        :param bool includeTermHierarchy: Must be True if you are using hierarchy or term templates.
        :param bool force_update: Currently not used.

        Kwargs:
            :param dict parameters: The parameters to pass into the url.

        :return: The uploaded term's current state.
        :rtype: dict        
        """
        return super().upload_term(
            term,
            force_update,
            parameters={
                "includeTermHierarchy": json.dumps(includeTermHierarchy)
            }
        )

    def upload_terms(self, terms, includeTermHierarchy=True, force_update=False, **kwargs):
        """
        Upload many terms to Azure Purview. However, if you
        plan on uploading many terms with many details, you might look at
        `PurviewClient.glossary.import_terms` instead which supports a csv
        upload.

        Provide a list of PurviewGlossaryTerms or dictionaries.

        :param terms: The term to be uploaded.
        :type terms: list(Union(:class:`~pyapacheatlas.core.glossary.term.PurviewGlossaryTerm`, dict))
        :param bool includeTermHierarchy: Must be True if you are using hierarchy or term templates.
        :param bool force_update: Currently not used.

        Kwargs:
            :param dict parameters: The parameters to pass into the url.

        :return: The uploaded terms' current states.
        :rtype: dict        
        """
        return super().upload_terms(
            terms,
            force_update,
            parameters={
                "includeTermHierarchy": json.dumps(includeTermHierarchy)
            }
        )

    # Import Term Section
    # Export Term Section
    def import_terms(self, csv_path, glossary_name="Glossary", glossary_guid=None):
        """
        Bulk import terms from an existing csv file. If you are using the system
        default, you must include the following headers:
        Name,Definition,Status,Related Terms,Synonyms,Acronym,Experts,Stewards

        For custom term templates, additional attributes must include
        [Attribute][termTemplateName]attributeName as the header.

        In the resulting JSON, you will receive an operation guid that can be
        passed to the `PurviewClient.glossary.import_terms_status` method to
        determine the success or failure of the import.

        :param str csv_path: Path to CSV that will be imported.
        :param str glossary_name:
            Name of the glossary. Defaults to 'Glossary'. Not used if
            glossary_guid is provided.
        :param str glossary_guid:
            Guid of the glossary, optional if glossary_name is provided.
            Otherwise, this parameter takes priority over glossary_name.

        :return:
            A dict that contains an `id` that you can use in
            `import_terms_status` to get the status of the import operation.
        :rtype: dict
        """
        results = None
        if glossary_guid:
            atlas_endpoint = self.endpoint_url + \
                f"/glossary/{glossary_guid}/terms/import?&includeTermHierarchy=True"
        elif glossary_name:
            atlas_endpoint = self.endpoint_url + \
                f"/glossary/name/{glossary_name}/terms/import?&includeTermHierarchy=True"
        else:
            raise ValueError(
                "Either glossary_name or glossary_guid must be defined.")

        headers = self.authentication.get_authentication_headers()
        # Pop the default of application/json so that request can fill in the
        # multipart/form-data; boundary=xxxx that is automatically generated
        # when using the files argument.
        headers.pop("Content-Type")

        postResp = requests.post(
            atlas_endpoint,
            files={'file': ("file", open(csv_path, 'rb'))},
            headers=headers,
            **self._requests_args
        )

        results = self._handle_response(postResp)

        return results

    def import_terms_status(self, operation_guid):
        """
        Get the operation status of a glossary term import activity. You get
        the operation_guid after executing the `import_terms` method and find
        the `id` field in the response dict/json.

        :param str operation_guid: The id of the import operation.
        :return: The status of the import operation as a dict. The dict includes
            a field called `status` that will report back RUNNING, SUCCESS, or
            FAILED. Other fields include the number of terms detected and
            number of errors.
        :rtype: dict
        """
        results = None
        atlas_endpoint = self.endpoint_url + \
            f"/glossary/terms/import/{operation_guid}"

        postResp = requests.get(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResp)

        return results

    def export_terms(self, guids, csv_path, glossary_name="Glossary", glossary_guid=None):
        """
        Export specific terms as provided by guid. Due to the design of Purview,
        you may not export terms with different term templates. Instead,
        you should batch exports based on the term template.

        This method writes the csv file to the provided path.

        :param list(str) guids: List of guids that should be exported as csv.
        :param str csv_path: Path to CSV that will be imported.
        :param str glossary_name:
            Name of the glossary. Defaults to 'Glossary'. Not used if
            glossary_guid is provided.
        :param str glossary_guid:
            Guid of the glossary, optional if glossary_name is provided.
            Otherwise, this parameter takes priority over glossary_name.
            Providing glossary_guid is also faster as you avoid a lookup based
            on glossary_name.

        :return: A csv file is written to the csv_path.
        :rtype: None
        """
        if glossary_guid:
            # Glossary guid is defined so we don't need to look up the guid
            pass
        elif glossary_name:
            glossary = self.get_glossary(glossary_name)
            glossary_guid = glossary["guid"]
        else:
            raise ValueError(
                "Either glossary_name or glossary_guid must be defined.")

        results = None
        atlas_endpoint = self.endpoint_url + \
            f"/glossary/{glossary_guid}/terms/export"

        postResp = requests.post(
            atlas_endpoint,
            json=guids,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        # Can't use handle response since it expects json
        try:
            postResp.raise_for_status()
        except requests.RequestException as e:
            if "errorCode" in postResp:
                raise AtlasException(postResp.text)
            else:
                raise requests.RequestException(postResp.text)

        with open(csv_path, 'wb') as fp:
            fp.write(postResp.content)

        return None
