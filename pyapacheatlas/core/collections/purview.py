import logging
from typing import List, Union

from ..entity import AtlasEntity
from ..util import _handle_response, AtlasBaseClient, batch_dependent_entities

import requests


class PurviewCollectionsClient(AtlasBaseClient):
    """
    Some support for purview collections api.

    See also:
    https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection

    """
    def __init__(self, endpoint_url : str, authentication, **kwargs):
        """
        :param str endpoint_url:
            Base URL for purview account, e.g. "https://{account}.purview.azure.com/" .
        """
        super().__init__(**kwargs)
        self.endpoint_url = endpoint_url
        self.authentication = authentication

    def upload_single_entity(
        self,
        entity : Union[AtlasEntity, dict],
        collection : str,
        api_version : str = "2022-03-01-preview"
    ):
        """
        Creates or updates a single atlas entity in a purview collection.

        See also
        https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection/create-or-update

        :param Union[AtlasEntity, dict] entity: The entity to create or update.
        :param str collection:
            Collection ID of the containing purview collection.
            Typically a 6-letter pseudo-random string such as "xcgw8s" which can be obtained
            e.g. by visual inspection in the purview web UI (https://web.purview.azure.com/).
        :param str api_version: The Purview API version to use.
        :return: An entity mutation response.
        :rtype: dict
        """

        atlas_endpoint = self.endpoint_url + f"catalog/api/collections/{collection}/entity"

        if isinstance(entity, AtlasEntity):
            payload = {"entity":entity.to_json(), "referredEntities":{}}
        elif isinstance(entity, dict):
            payload = entity
        else:
            raise ValueError("entity should be an AtlasEntity or dict")

        singleEntityResponse = requests.post(
            atlas_endpoint,
            json = payload,
            params = {"api-version": api_version},
            headers = self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(singleEntityResponse)
        return results

    def upload_entities(
        self,
        batch : List[AtlasEntity],
        collection : str,
        batch_size : int = None,
        api_version : str = "2022-03-01-preview"
    ):
        """
        Creates or updates a batch of atlas entities in a purview collection.

        See also
        https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection/create-or-update-bulk

        :param batch:
            The batch of entities you want to upload. Supports a single dict,
            AtlasEntity, list of dicts, list of atlas entities.
        :type batch:
            Union(dict, :class:`~pyapacheatlas.core.entity.AtlasEntity`,
            list(dict), list(:class:`~pyapacheatlas.core.entity.AtlasEntity`) )
        :param str collection:
            Collection ID of the containing purview collection.
            Typically a 6-letter pseudo-random string such as "xcgw8s" which can be obtained
            e.g. by visual inspection in the purview web UI (https://web.purview.azure.com/).
        :param int batch_size: The number of entities you want to send in bulk.
        :param str api_version: The Purview API version to use.
        :return: An entity mutation response.
        :rtype: dict
        """

        atlas_endpoint = self.endpoint_url + f"catalog/api/collections/{collection}/entity/bulk"

        payload = PurviewCollectionsClient._prepare_entity_upload(batch)
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
                    params = {"api-version": api_version},
                    headers=self.authentication.get_authentication_headers(),
                    **self._requests_args
                )
                temp_results = _handle_response(postBulkEntities)
                results.append(temp_results)

        else:
            postBulkEntities = requests.post(
                atlas_endpoint,
                json=payload,
                params = {"api-version": api_version},
                headers=self.authentication.get_authentication_headers(),
                **self._requests_args
            )

            results = _handle_response(postBulkEntities)

        return results
    
    # TODO: This is duplication with the AtlasClient and should eventually be removed
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

    def move_entities(
        self,
        guids : List[str],
        collection : str,
        api_version : str = "2022-03-01-preview"
    ):
        """
        Move one or more entities based on their guid to the provided collection.

        See also
        https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection/move-entities-to-collection

        :param str collection:
            Collection ID of the containing purview collection.
            Typically a 6-letter pseudo-random string such as "xcgw8s" which can be obtained
            e.g. by visual inspection in the purview web UI (https://web.purview.azure.com/).
        :param str api_version: The Purview API version to use.
        :return: An entity mutation response.
        :rtype: dict
        """

        atlas_endpoint = self.endpoint_url + f"catalog/api/collections/{collection}/entity/moveHere"

        singleEntityResponse = requests.post(
            atlas_endpoint,
            json = {"entityGuids":guids},
            params = {"api-version": api_version},
            headers = self.authentication.get_authentication_headers(),
            **self._requests_args
        )
        results = _handle_response(singleEntityResponse)
        return results

    def _list_collections_generator(self, initial_endpoint):
        """
        Generator to page through the list collections response
        """
        updated_endpoint = initial_endpoint
        while True:
            if updated_endpoint is None:
                return
            collectionsListGet = requests.get(
                updated_endpoint,
                headers = self.authentication.get_authentication_headers(),
                **self._requests_args
            )

            results = _handle_response(collectionsListGet)

            return_values = results["value"]
            return_count = len(return_values)
            updated_endpoint = results.get("nextLink")

            if return_count == 0:
                return

            for sub_result in return_values:
                try:
                    yield sub_result
                except StopIteration:
                    return

    def list_collections(
        self,
        api_version : str = "2019-11-01-preview",
        skipToken : str = None
    ):
        """
        List the collections in the account.

        :param str api_version: The Purview API version to use.
        :param str skipToken: It is unclear at this time what values would be
            provided to this parameter.
        :return: A generator that pages through the list collections
        :rtype: List[dict]
        """
        atlas_endpoint = self.endpoint_url + f"collections?api-version={api_version}"
        if skipToken:
            atlas_endpoint = atlas_endpoint + f"&$skipToken={skipToken}"

        collection_generator = self._list_collections_generator(atlas_endpoint)

        return collection_generator