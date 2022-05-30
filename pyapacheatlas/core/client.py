from .util import AtlasException, AtlasBaseClient, batch_dependent_entities, PurviewLimitation, PurviewOnly, _handle_response
from .collections.purview import PurviewCollectionsClient
from .glossary import _CrossPlatformTerm, GlossaryClient, PurviewGlossaryClient
from .discovery.purview import PurviewDiscoveryClient
from .typedef import BaseTypeDef, TypeCategory
from .msgraph import MsGraphClient
from .entity import AtlasClassification, AtlasEntity
from ..auth.base import AtlasAuthBase
import logging
import re
import requests
import warnings
import sys
_AZ_IDENTITY_INSTALLED = False
try:
    import azure.identity
    _AZ_IDENTITY_INSTALLED = True
    from ..auth.azcredential import AzCredentialWrapper
except ImportError:
    pass


class AtlasClient(AtlasBaseClient):
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
    
    Kwargs:
        :param requests_*: 
            Kwargs to pass to the underlying `requests` package method call.
            For example passing `requests_verify = False` will supply `verify=False`
            to any API call.
    """

    def __init__(self, endpoint_url, authentication=None, **kwargs):
        self.authentication = authentication
        self.endpoint_url = endpoint_url
        self.is_purview = False
        self._purview_url_pattern = r"https:\/\/[a-z0-9-]*?\.(catalog\.purview.azure.com)"
        if re.match(self._purview_url_pattern, self.endpoint_url):
            self.is_purview = True
        # If requests_verify=False is provided, it will result in
        # storing verify:False in the _requests_args
        if "requests_args" not in kwargs:
            requests_args = AtlasClient._parse_requests_args(**kwargs)
        else:
            requests_args = kwargs.pop("requests_args")
        
        if "glossary" not in kwargs:
            self.glossary = GlossaryClient(endpoint_url, authentication, requests_args=requests_args)
        else:
            self.glossary = kwargs["glossary"]

        super().__init__(requests_args = requests_args)

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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
            )

        results = _handle_response(deleteEntity)

        return results

    def delete_businessMetadata(self, guid, businessMetadata, force_update=True):
        """
        Delete one or many business attributes based on the guid. Provide a
        businessMetadata dictionary that has a key for the businessmetadata
        type def name and the value is a dictionary with keys of each
        attribute you want to remove. The values inside the nested dict
        should be an empty string ('').

        If I have a business metadata typedef of 'operations`, with attributes
        'expenseCode' and 'criticality' and I want to delete criticality, my
        businessMetadata might be:
        ```
        {
            'operations': {
                'criticality': ''
          }
        }
        ```

        :param str guid:
            The guid for the entity that you want to remove business metadata.
        :param dict(str, dict) businessMetadata:
            The business metadata you want to delete with key of the
            businessMetadata type def and value of a dictionary with
            keys for each attribute you want removed and value is an empty
            string.
        :param bool force_update:
            Defaults to True.
        :return:
            A dictionary indicating success. Failure will raise an AtlasException.
        :rtype: dict
        """
        results = None

        atlas_endpoint = self.endpoint_url + \
            f"/entity/guid/{guid}/businessmetadata"
        deleteBizMeta = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers(),
            params={"isOverwrite":force_update},
            json=businessMetadata,
            **self._requests_args
            )

        try:
            deleteBizMeta.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteBizMeta.text)

        results = {
            "message": f"Successfully deleted businessMetadata on entity with guid {guid}"}
        return results

    def delete_relationship(self, guid):
        """
        Delete a relationship based on the guid. This lets you remove
        a connection between entities like removing a column from a
        table or a term from an entity.

        :param str guid:
            The relationship guid for the relationship that you want to remove.
        :return:
            A dictionary indicating success. Failure will raise an AtlasException.
        :rtype: dict
        """
        results = None

        atlas_endpoint = self.endpoint_url + \
            f"/relationship/guid/{guid}"
        deleteType = requests.delete(
            atlas_endpoint,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
            )

        try:
            deleteType.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteType.text)

        results = {
            "message": f"Successfully deleted relationship with guid {guid}"}
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
            )

        try:
            deleteType.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteType.text)

        results = {"message": f"successfully delete {name}"}
        return results

    def delete_typedefs(self, **kwargs):
        """
        Delete one or many types. You can provide a parameters as listed in the
        kwargs. You'll pass in a type definition that you want to delete.

        That type def can be retrieved with `AtlasClient.get_typedef` or by
        creating the typedef with, for example `EntityTypeDef("someType")` as
        imported from :class:`~pyapacheatlas.core.typedef.EntityTypeDef`. You
        do not need to include any attribute defs, even if they're required.

        Kwargs:
            :param entityDefs: EntityDefs to delete.
            :type entityDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param businessMetadataDefs: BusinessMetadataDefs to delete.
            :type businessMetadataDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param classificationDefs: classificationDefs to delete.
            :type classificationDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param enumDefs: enumDefs to delete.
            :type enumDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param relationshipDefs: relationshipDefs to delete.
            :type relationshipDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
            :param structDefs: structDefs to delete.
            :type structDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))

        :return:
            A dictionary indicating success. Failure will raise an AtlasException.
        :rtype: dict
        """
        results = None
        payload = {}
        allowed_defs = [
            "businessMetadataDefs", "classificationDefs", "entityDefs",
            "enumDefs", "relationshipDefs", "structDefs"]
        if len(set(kwargs.keys()).intersection(allowed_defs)) == 0:
            raise TypeError(
                f"You must include one of these keyword arguments: {allowed_defs}")

        for defType in allowed_defs:
            if defType in kwargs:
                # Should be a list
                json_list = [t.to_json() if isinstance(
                    t, BaseTypeDef) else t for t in kwargs[defType]]
                payload[defType] = json_list

        atlas_endpoint = self.endpoint_url + \
            "/types/typedefs"
        deleteType = requests.delete(
            atlas_endpoint,
            json=payload,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
            )

        try:
            deleteType.raise_for_status()
        except requests.RequestException:
            raise Exception(deleteType.text)

        results = {"message": f"Successfully deleted type(s)"}
        return results

    def get_entity(self, guid=None, qualifiedName=None, typeName=None, ignoreRelationships=False, minExtInfo=False):
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
        :param bool ignoreRelationships:
            Exclude the relationship information from the response.
        :param bool minExtInfo:
            Exclude the extra information from the response.
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

        # Support the adding or removing of relationships and extra info
        parameters.update(
            {"ignoreRelationships": ignoreRelationships, "minExtInfo": minExtInfo})
        getEntity = requests.get(
            atlas_endpoint,
            params=parameters,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getEntity)

        return results

    def get_single_entity(self, guid=None, ignoreRelationships=False, minExtInfo=False):
        """
        Retrieve one entity based on guid from your Atlas backed Data Catalog.

        Returns a dictionary with keys "referredEntities" and "entity". You'll
        want to grab the entity value which is a single dictionary.

        :param str guid: The guid you want to retrieve.
        :param bool ignoreRelationships:
            Exclude the relationship information from the response.
        :param bool minExtInfo:
            Exclude the extra information from the response.
        :return:
            An AtlasEntityWithExtInfo object which includes "referredEntities"
            and "entity" keys.
        :rtype: dict(str, Union(list(dict),dict))
        """
        results = None
        parameters = {}

        atlas_endpoint = self.endpoint_url + \
            "/entity/guid/{}".format(guid)

        # Support the adding or removing of relationships and extra info
        parameters.update(
            {"ignoreRelationships": ignoreRelationships, "minExtInfo": minExtInfo})
        getEntity = requests.get(
            atlas_endpoint,
            params=parameters,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getEntity)

        return results

    def partial_update_entity(self, guid=None, typeName=None, qualifiedName=None, attributes={}):
        """
        Partially update an entity without having to construct the entire object
        and its subsequent required attributes. Using guid, you can update a
        single attribute. Using typeName and qualifiedName, you can update
        multiple attributes.

        :param guid:
            The guid for the entity you want to update. Not used if using
            typeName and qualifiedName.
        :type guid: str
        :param qualifiedName:
            The qualified name of the entity you want to update. Must provide
            typeName if using qualifiedName. Ignored if using guid parameter.
        :type qualifiedName: str
        :param str typeName:
            The type name of the entity you want to update. Must provide
            qualifiedName if using typeName. Ignored if using guid parameter.
        :return: The results of your entity update.
        :rtype: dict
        """

        if guid and len(attributes) == 1:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/guid/{guid}"
            attribute_name = list(attributes.keys())[0]
            attribute_value = attributes[attribute_name]
            putEntity = requests.put(
                atlas_endpoint,
                json=attribute_value,
                params={"name": attribute_name},
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )
        # TODO: Multiple attributes could be supported for guid by looking up
        # the qualified name and type and then re-running the command with
        # those parameters.
        elif guid:
            raise ValueError(
                "When using guid, attributes can only contain one key and value.")
        elif typeName and qualifiedName:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/uniqueAttribute/type/{typeName}"
            # You have to get the entire existing entity and update its attributes
            get_response = self.get_entity(
                qualifiedName=qualifiedName, typeName=typeName)
            try:
                entity = get_response["entities"][0]
            except KeyError:
                raise ValueError(
                    f"The entity with qualifiedName {qualifiedName} and type {typeName} does not exist and cannot be updated.")
            entity["attributes"].update(attributes)
            # Construct it as an AtlasEntityWithInfo
            entityInfo = {"entity": entity,
                          "referredEntities": get_response["referredEntities"]}

            putEntity = requests.put(
                atlas_endpoint,
                json=entityInfo,
                params={"attr:qualifiedName": qualifiedName},
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )
        else:
            raise ValueError(
                "The provided combination of arguments is not supported. Either provide a guid or type name and qualified name")

        results = _handle_response(putEntity)

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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(getClassification)
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getClassification)

        return results

    def get_entity_header(self, guid=None):
        """
        Retrieve one or many entity headers from your Atlas backed Data Catalog.

        :param guid:
            The guid or guids you want to retrieve.
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getEntity)

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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getResponse)

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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getTypeDefs)

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
            # business_Metadata has an underscore so before it can be used in
            # the endpoint, it must be converted to businessMetadata.
            atlas_endpoint = atlas_endpoint + \
                "{}def".format(type_category.value.replace("_", ""))
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(getTypeDef)

        return results

    def get_glossary(self, name="Glossary", guid=None, detailed=False):
        """
        AtlasClient.get_glossary is being deprecated.
        Please use AtlasClient.glossary.get_glossary instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.get_glossary is being deprecated. Please use AtlasClient.glossary.get_glossary instead.")
        results = self.glossary.get_glossary(name, guid, detailed)
        return results

    def get_glossary_term(self, guid=None, name=None, glossary_name="Glossary", glossary_guid=None):
        """
        AtlasClient.get_glossary_term is being deprecated.
        Please use AtlasClient.glossary.get_term instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.get_glossary_term is being deprecated. Please use AtlasClient.glossary.get_term instead.")
        results = self.glossary.get_term(
            guid, name, glossary_name, glossary_guid)
        return results

    def assignTerm(self, entities, termGuid=None, termName=None, glossary_name="Glossary"):
        """
        AtlasClient.assignTerm is being deprecated.
        Please use AtlasClient.glossary.assignTerm instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.assignTerm is being deprecated. Please use AtlasClient.glossary.assignTerm instead.")
        results = self.glossary.assignTerm(
            entities, termGuid, termName, glossary_name)
        return results

    def delete_assignedTerm(self, entities, termGuid=None, termName=None, glossary_name="Glossary"):
        """
        AtlasClient.delete_assignedTerm is being deprecated.
        Please use AtlasClient.glossary.delete_assignedTerm instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.delete_assignedTerm is being deprecated. Please use AtlasClient.glossary.delete_assignedTerm instead.")
        results = self.glossary.delete_assignedTerm(
            entities, termGuid, termName, glossary_name)
        return results

    def get_termAssignedEntities(self, termGuid=None, termName=None, glossary_name="Glossary", limit=-1, offset=0, sort="ASC"):
        """
        AtlasClient.get_termAssignedEntities is being deprecated.
        Please use AtlasClient.glossary.get_termAssignedEntities instead.

        Page through the assigned entities for the given term.

        :param str termGuid: The guid for the term. Ignored if using termName.
        :param str termName: The name of the term. Optional if using termGuid.
        :param str glossary_name:
            The name of the glossary. Defaults to Glossary. Ignored if using termGuid.

        :return: A list of Atlas relationships between the given term and entities.
        :rtype: list(dict)
        """
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.get_termAssignedEntities is being deprecated. Please use AtlasClient.glossary.get_termAssignedEntities instead.")
        results = self.glossary.get_termAssignedEntities(
            termGuid, termName, glossary_name, limit, offset, sort)
        return results

    def upload_terms(self, batch, force_update=False):
        """
        AtlasClient.upload_terms is being deprecated.
        Please use AtlasClient.glossary.upload_terms instead.

        Upload terms to your Atlas backed Data Catalog. Supports Purview Term
        Templates by passing in an attributes field with the term template's
        name as a field within attributes and an object of the required and
        optional fields.

        :param batch: A list of AtlasGlossaryTerm objects to be uploaded.
        :type batch: list(dict)
        :return:
            A list of AtlasGlossaryTerm objects that are the results from
            your upload.
        :rtype: list(dict)
        """
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "AtlasClient.upload_terms is being deprecated. Please use AtlasClient.glossary.upload_terms instead.")
        results = self.glossary.upload_terms(batch, force_update)
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(getHeaders)

        output = dict()
        for typedef in results:
            if typedef["category"].lower() == TypeCategory.BUSINESSMETADATA.value.lower():
                active_category = "businessMetadataDefs"
            else:
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
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
    def _prepare_type_upload(typedefs=None, **kwargs):
        """
        Massage the type upload. See rules in upload_typedefs.
        """
        payload = {}
        required_keys = ["businessMetadataDefs", "classificationDefs", "entityDefs",
                         "enumDefs", "relationshipDefs", "structDefs"]

        # If typedefs is defined as a dict and it contains at least one of the
        # required keys for the TypeREST definition.
        if isinstance(typedefs, dict) and len(set(typedefs.keys()).intersection(required_keys)) > 0:
            payload = typedefs
        # It isn't in the standard form but is it defined?
        elif typedefs is not None:
            # Assuming this is a single typedef
            key = None
            if isinstance(typedefs, BaseTypeDef):
                key = typedefs.category
                val = [typedefs.to_json()]
            elif isinstance(typedefs, dict):
                key = typedefs["category"]
                val = [typedefs]
            else:
                raise NotImplementedError(
                    "Uploading an object of type '{}' is not supported."
                    .format(type(typedefs))
                )

            # business_metadata must be converted to businessMetadataDefs
            # but it's stored as BUSINESS_METADATA
            key = key.lower()
            if key == "business_metadata":
                key = "businessMetadata"
            key = key + "Defs"
            payload = {key: val}
        # Did we set any of the xDefs as arguments?
        elif len(set(kwargs.keys()).intersection(required_keys)) > 0:
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

    def upload_typedefs(self, typedefs=None, force_update=False, **kwargs):
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
            :param businessMetadataDefs: businessMetadataDefs to upload.
            :type businessMetadataDefs: list( Union(:class:`~pyapacheatlas.core.typedef.BaseTypeDef`, dict))
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
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )
            results = _handle_response(upload_typedefs_results)
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

            results_new = {}
            if new_types and sum([len(defs) for defs in new_types.values()]) > 0:
                upload_new = requests.post(
                    atlas_endpoint, json=new_types,
                    headers=self.authentication.get_authentication_headers(),
                    **self._requests_args
                )
                results_new = _handle_response(upload_new)

            results_exist = {}
            if existing_types and sum([len(defs) for defs in existing_types.values()]) > 0:
                upload_exist = requests.put(
                    atlas_endpoint, json=existing_types,
                    headers=self.authentication.get_authentication_headers(),
                    **self._requests_args
                )
                results_exist = _handle_response(upload_exist)

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
            dict_batch = [e.to_json() if isinstance(
                e, AtlasEntity) else e for e in batch]
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
            raise NotImplementedError(
                f"Uploading type: {type(batch)} is not supported.")

        return payload

    def upload_entities(self, batch, batch_size=None):
        """
        Upload entities to your Atlas backed Data Catalog.

        :param batch:
            The batch of entities you want to upload. Supports a single dict,
            AtlasEntity, list of dicts, list of atlas entities.
        :type batch:
            Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`,
            list(dict), list(:class:`~pyapacheatlas.core.entity.AtlasEntity`) )
        :param int batch_size: The number of entities you want to send in bulk
        :return: The results of your bulk entity upload.
        :rtype: dict
        """
        # TODO Include a Do Not Overwrite call
        results = None
        atlas_endpoint = self.endpoint_url + "/entity/bulk"

        payload = AtlasClient._prepare_entity_upload(batch)

        results = []
        if batch_size and len(payload["entities"]) > batch_size:
            batches = [{"entities": x} for x in batch_dependent_entities(
                payload["entities"], batch_size=batch_size)]

            for batch_id, batch in enumerate(batches):
                batch_size = len(batch["entities"])
                logging.debug(f"Batch upload #{batch_id} of size {batch_size}")
                postBulkEntities = requests.post(
                    atlas_endpoint,
                    json=batch,
                    headers=self.authentication.get_authentication_headers(),
                    **self._requests_args
                )
                temp_results = _handle_response(postBulkEntities)
                results.append(temp_results)

        else:
            postBulkEntities = requests.post(
                atlas_endpoint,
                json=payload,
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )

            results = _handle_response(postBulkEntities)

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
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = _handle_response(relationshipResp)

        return results

    # TODO: Remove at 1.0.0 release
    def _search_generator(self, search_params, starting_offset=0):
        """
        Generator to page through the search query results.
        """
        atlas_endpoint = self.endpoint_url + "/search/advanced"
        offset = starting_offset

        while True:
            postSearchResults = requests.post(
                atlas_endpoint,
                json=search_params,
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )
            results = _handle_response(postSearchResults)
            return_values = results["value"]
            return_count = len(return_values)

            if return_count == 0:
                return

            offset = offset + return_count
            search_params["offset"] = offset

            for sub_result in return_values:
                try:
                    yield sub_result
                except StopIteration:
                    return

    @PurviewOnly
    def search_entities(self, query, limit=50, search_filter=None, starting_offset=0):
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
        :rtype: Iterator(dict)
        """
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "PurviewClient.search_entities is being deprecated. Please use PurviewClient.discovery.search_entities instead.")

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

        search_generator = self._search_generator(
            search_params, starting_offset=starting_offset)

        return search_generator

    def get_entity_lineage(self, guid, depth=3, width=10, direction="BOTH", includeParent=False, getDerivedLineage=False):
        """
        Gets lineage info about the specified entity by guid.

        :param str guid: The guid of the entity for which you want to
            retrieve lineage.
        :param int depth: The number of hops for lineage
        :param int width: The number of max expanding width in lineage
        :param str direction: The direction of the lineage, which could
            be INPUT, OUTPUT or BOTH.
        :param bool includeParent: True to include the parent chain in
            the response
        :param bool getDerivedLineage: True to include derived lineage in
            the response
        :return: A dict representing AtlasLineageInfo with an array
            of parentRelations and an array of relations
        :rtype: dict(str, dict)
        """
        direction = direction.strip().upper()
        assert direction in (
            "BOTH", "INPUT", "OUTPUT"), "Invalid direction '{}'.  Valid options are: BOTH, INPUT, OUTPUT".format(direction)

        atlas_endpoint = self.endpoint_url + \
            f"/lineage/{guid}"

        getLineageRequest = requests.get(
            atlas_endpoint,
            params={"depth": depth, "width": width, "direction": direction,
                    "includeParent": includeParent, "getDerivedLineage": getDerivedLineage},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(getLineageRequest)
        return results

    def delete_entity_labels(self, labels, guid=None, typeName=None, qualifiedName=None):
        """
        Delete the given labels for one entity. Provide a list of strings that
        should be removed. You can either provide the guid of the entity or
        the typeName and qualifiedName of the entity.

        If you want to clear out an entity without knowing all the labels, you
        should consider `update_entity_labels` instead and set
        force_update to True.

        :param list(str) labels: The label(s) that should be removed.
        :param str guid:
            The guid of the entity to be updated. Optional if using typeName
            and qualifiedName.
        :param str typeName:
            The type name of the entity to be updated. Must also use
            qualifiedname with typeName. Not used if guid is provided.
        :param str qualifiedName:
            The qualified name of the entity to be updated. Must also use
            typeName with qualifiedName. Not used if guid is provided.
        :return:
            A dict containing a message indicating success. Otherwise
            it will raise an AtlasException.
        :rtype: dict(str, str)
        """

        parameters = {}
        if guid:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/guid/{guid}/labels"
        elif qualifiedName and typeName:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/uniqueAttribute/type/{typeName}/labels"
            parameters.update({"attr:qualifiedName": qualifiedName})
        else:
            raise ValueError(
                "Either guid or typeName and qualifiedName must be defined.")

        deleteResp = requests.delete(
            atlas_endpoint,
            params=parameters,
            json=labels,
            headers=self.authentication.get_authentication_headers())

        # Can't use _handle_response since it expects json returned
        try:
            deleteResp.raise_for_status()
        except requests.RequestException as e:
            if "errorCode" in deleteResp:
                raise AtlasException(deleteResp.text)
            else:
                raise requests.RequestException(deleteResp.text)

        action = f"guid: {guid}" if guid else f"type:{typeName} qualifiedName:{qualifiedName}"
        results = {"message": f"Successfully deleted labels for {action}"}
        return results

    def update_entity_labels(self, labels, guid=None, typeName=None, qualifiedName=None, force_update=False):
        """
        Update the given labels for one entity. Provide a list of strings that
        should be added. You can either provide the guid of the entity or
        the typeName and qualifiedName of the entity. By using force_update
        set to True you will overwrite the existing entity. force_update
        set to False will append to the existing entity.

        :param list(str) labels: The label(s) that should be appended or set.
        :param str guid:
            The guid of the entity to be updated. Optional if using typeName
            and qualifiedName.
        :param str typeName:
            The type name of the entity to be updated. Must also use
            qualifiedname with typeName. Not used if guid is provided.
        :param str qualifiedName:
            The qualified name of the entity to be updated. Must also use
            typeName with qualifiedName. Not used if guid is provided.
        :return:
            A dict containing a message indicating success. Otherwise
            it will raise an AtlasException.
        :rtype: dict(str, str)
        """

        parameters = {}
        if guid:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/guid/{guid}/labels"
        elif qualifiedName and typeName:
            atlas_endpoint = self.endpoint_url + \
                f"/entity/uniqueAttribute/type/{typeName}/labels"
            parameters.update({"attr:qualifiedName": qualifiedName})
        else:
            raise ValueError(
                "Either guid or typeName and qualifiedName must be defined.")

        verb = "added"
        if force_update:
            updateResp = requests.post(
                atlas_endpoint,
                params=parameters,
                json=labels,
                headers=self.authentication.get_authentication_headers())
            verb = "overwrote"
        else:
            updateResp = requests.put(
                atlas_endpoint,
                params=parameters,
                json=labels,
                headers=self.authentication.get_authentication_headers())

        # Can't use _handle_response since it expects json returned
        try:
            updateResp.raise_for_status()
        except requests.RequestException as e:
            if "errorCode" in updateResp:
                raise AtlasException(updateResp.text)
            else:
                raise requests.RequestException(updateResp.text)

        action = f"guid: {guid}" if guid else f"type:{typeName} qualifiedName:{qualifiedName}"
        results = {"message": f"Successfully {verb} labels for {action}"}
        return results

    def update_businessMetadata(self, guid, businessMetadata, force_update=False):
        """
        Update the business metadata. Provide a businessMetadata dictionary
        that has a key for the businessmetadata type def name and the value
        is a dictionary with keys of each attribute you want to add/update.

        If I have a business metadata typedef of 'operations`, with attributes
        'expenseCode' and 'criticality', my businessMetadata might be:
        ```
        {
            'operations': {
                'expenseCode': '123',
                'criticality': 'low'
          }
        }
        ```
        :param str guid:
            The guid for the entity that you want to update business metadata.
        :param dict(str, dict) businessMetadata:
            The business metadata you want to update with key of the
            businessMetadata type def and value of a dictionary with
            keys for each attribute you want removed and value
        :param bool force_update:
            Defaults to False where you are only overwriting the business
            attributes you specify in businessMetadata. Set to True to
            overwrite all existing business metadata attributes with the value
            you provided.
        :return:
            A dict containing a message indicating success. Otherwise
            it will raise an AtlasException.
        :rtype: dict(str, str)
        """
        atlas_endpoint= self.endpoint_url + f"/entity/guid/{guid}/businessmetadata"
        updateBizMeta = requests.post(
            atlas_endpoint,
            params={"isOverwrite":force_update},
            json=businessMetadata,
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        # Can't use _handle_response since it expects json returned
        try:
            updateBizMeta.raise_for_status()
        except requests.RequestException as e:
            if isinstance(updateBizMeta, dict) and "errorCode" in updateBizMeta:
                raise AtlasException(updateBizMeta.text)
            else:
                raise requests.RequestException(updateBizMeta.text)

        return {"message": f"Successfully updated business metadata for {guid}"}


class PurviewClient(AtlasClient):
    """
    Provides communication between your application and the Azure Purview
    service. Simplifies the requirements for knowing the endpoint url and
    requires only the Purview account name.

    See also:
    https://docs.microsoft.com/en-us/rest/api/purview/

    :param str account_name:
        Your Purview account name.
    :param authentication:
        The method of authentication.
    :type authentication:
        :class:`~pyapacheatlas.auth.base.AtlasAuthBase`
    
    Kwargs:
        :param requests_*: 
            Kwargs to pass to the underlying `requests` package method call.
            For example passing `requests_verify = False` will supply `verify=False`
            to any API call.
    """

    def __init__(self, account_name, authentication=None, **kwargs):
        endpoint_url = f"https://{account_name.lower()}.catalog.purview.azure.com/api/atlas/v2"
        if authentication and not isinstance(authentication, AtlasAuthBase):
            # Assuming this is Azure Identity related
            if _AZ_IDENTITY_INSTALLED:
                authentication = AzCredentialWrapper(authentication)
            else:
                raise Exception(
                    "You probably need to install azure-identity to use this authentication method.")
        if "requests_args" in kwargs:
            requests_args = kwargs.pop("requests_args")
        else:
            requests_args = AtlasBaseClient._parse_requests_args(**kwargs)

        glossary = PurviewGlossaryClient(endpoint_url, authentication, requests_args = requests_args)
        self.collections = PurviewCollectionsClient(f"https://{account_name.lower()}.purview.azure.com/", authentication, requests_args = requests_args)
        self.msgraph = MsGraphClient(authentication, requests_args = requests_args)
        self.discovery = PurviewDiscoveryClient(f"https://{account_name.lower()}.purview.azure.com/catalog/api", authentication, requests_args = requests_args)
        super().__init__(endpoint_url, authentication, glossary = glossary, requests_args = requests_args, **kwargs)

    @PurviewOnly
    def get_entity_next_lineage(self, guid, direction, getDerivedLineage=False, offset=0, limit=-1):
        """
        Returns immediate next level lineage info about entity with pagination

        See also:
        https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/lineage

        :param str guid: The guid of the entity for which you want to
            retrieve lineage.
        :param str direction: The direction of the lineage, which could
            be INPUT or OUTPUT.
        :param bool getDerivedLineage: True to include derived lineage in
            the response
        :param int offset: The offset for pagination purpose.
        :param int limit: The page size - by default there is no paging.
        :return: A dict representing AtlasLineageInfo with an array
            of parentRelations and an array of relations
        :rtype: dict(str, dict)
        """
        direction = direction.strip().upper()
        assert direction in (
            "INPUT", "OUTPUT"), "Invalid direction '{}'.  Valid options are: INPUT, OUTPUT".format(direction)

        atlas_endpoint = self.endpoint_url + \
            f"/lineage/{guid}/next"

        # TODO: Implement paging with offset and limit
        getLineageRequest = requests.get(
            atlas_endpoint,
            params={"direction": direction, "getDerivedLineage": getDerivedLineage,
                    "offset": offset, "limit": limit},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(getLineageRequest)
        return results

    def import_terms(self, csv_path, glossary_name="Glossary", glossary_guid=None):
        """
        Bulk import terms from an existing csv file. If you are using the system
        default, you must include the following headers:
        Name,Definition,Status,Related Terms,Synonyms,Acronym,Experts,Stewards

        For custom term templates, additional attributes must include
        [Attribute][termTemplateName]attributeName as the header.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "PurviewClient.import_terms is being deprecated. Please use PurviewClient.glossary.import_terms instead.")
        results = self.glossary.import_terms(
            csv_path, glossary_name, glossary_guid)
        return results

    @PurviewOnly
    def import_terms_status(self, operation_guid):
        """
        PurviewClient.import_terms_status is being deprecated.
        Please use PurviewClient.glossary.import_terms_status instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "PurviewClient.import_terms_status is being deprecated. Please use PurviewClient.glossary.import_terms_status instead.")
        results = self.glossary.import_terms_status(operation_guid)
        return results

    @PurviewOnly
    def export_terms(self, guids, csv_path, glossary_name="Glossary", glossary_guid=None):
        """
        PurviewClient.export_terms is being deprecated.
        Please use PurviewClient.glossary.export_terms instead.

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
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "PurviewClient.export_terms is being deprecated. Please use PurviewClient.glossary.export_terms instead.")
        results = self.glossary.export_terms(
            guids, csv_path, glossary_name, glossary_guid)
        return results

    def upload_term(self, term, includeTermHierarchy=True, **kwargs):
        """
        PurviewClient.upload_term is being deprecated.
        Please use PurviewClient.glossary.upload_term instead.

        Upload a single term to Azure Purview. Minimally, you can specify
        the term alone and it will upload it to Purview! However, if you
        plan on uploading many terms programmatically, you might look at
        `PurviewClient.upload_terms` or `PurviewClient.import_terms`.

        If you do intend on using this method for multiple terms consider
        looking up the glossary_guid and any parent term guids in advance
        otherwise, this method will call get_glossary multiple times making
        it much slower to do many updates.

        ```
        glossary = client.get_glossary()
        glossary_guid = glossary["guid"]
        ```
        """
        # TODO: Remove at 1.0.0 release
        warnings.warn(
            "PurviewClient.upload_term is being deprecated. Please use PurviewClient.glossary.upload_term instead.")
        results = self.glossary.upload_term(term, includeTermHierarchy)
        return results
