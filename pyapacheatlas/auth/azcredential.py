from datetime import datetime
import json
import requests

from .base import AtlasAuthBase
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError


class AzCredentialWrapper(AtlasAuthBase):
    """
    Thin wrapper around azure.core.credentials.TokenCredential
    """

    def __init__(self, credential):
        """
        :param azure.core.credentials.TokenCredential credential:
            The azure-identity credential you've provided. You most
            likely want to provide the DefaultAzureCredential().
        """
        super().__init__()

        self._resource_scope = "73c2949e-da2d-457a-9607-fcc665198967/.default"
        self._credential = credential
        self.access_token = None
        self.expiration = datetime.now()

    def _set_access_token(self):
        """
        Sets the access token for your session.
        """

        token_req = self._credential.get_token(self._resource_scope)
        self.access_token = token_req.token
        self.expiration = datetime.fromtimestamp(token_req.expires_on)

    def get_authentication_headers(self):
        """
        Gets the current access token or refreshes the token if it
        has expired.
        :return: The authorization headers.
        :rtype: dict(str, str)
        """
        if self.expiration <= datetime.now():
            self._set_access_token()

        return {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }
