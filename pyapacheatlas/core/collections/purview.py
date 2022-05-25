from ..entity import AtlasEntity
import requests


class PurviewCollectionsClient():
    """
    Some support for purview collections api.

    See also:
    https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection

    """
    def __init__(self, endpoint_url : str, authentication):
        """
        :param str endpoint_url:
            Base URL for purview account, e.g. "https://{account}.purview.azure.com/" .
        """
        self.endpoint_url = endpoint_url
        self.authentication = authentication

    def createOrUpdateToCollection(
        self,
        collection : str,
        entity : AtlasEntity,
        api_version : str = "2021-05-01-preview"
    ):
        """
        Creates or updates a single atlas entity in a purview collection.

        See also
        https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection/create-or-update

        :param str collection:
            Collection ID of the containing purview collection.
            Typically a 6-letter pseudo-random string such as "xcgw8s" which can be obtained
            e.g. by visual inspection in the purview web UI (https://web.purview.azure.com/).

        :param AtlasEntity entity: The entity to create or update.
        :param str api_version: The Purview API version to use.
        :return: Autocomplete Search results with a value field.
        :rtype: dict
        """

        atlas_endpoint = self.endpoint_url + f"catalog/api/collections/{collection}/entity"

        return requests.post(
            atlas_endpoint,
            json = entity.to_json(),
            params = {"api-version": api_version},
            headers = self.authentication.get_authentication_headers(),
            **self._requests_args
        )
