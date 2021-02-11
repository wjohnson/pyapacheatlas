from datetime import datetime
import json
import requests

from .base import AtlasAuthBase


class ServicePrincipalAuthentication(AtlasAuthBase):
    """
    Authenticates to the Azure OAuth provider using a service principal.
    """

    def __init__(self, tenant_id, client_id, client_secret):
        """
        :param str tenant_id: The tenant id of your Azure subscription.
        :param str client_id: The client id or application id of your
            service principal.
        :param str client_secret: The client secret or application secret
            of your service principal.
        """
        super().__init__()

        self.ouath_url = (
            "https://login.microsoftonline.com/" +
            tenant_id + "/oauth2/token"
        )
        self.data = {
            # This is the resource id for the data catalog
            "resource": "73c2949e-da2d-457a-9607-fcc665198967",
            "client_id": client_id,
            "grant_type": "client_credentials",
            "client_secret": client_secret
        }
        self.access_token = None
        self.expiration = datetime.now()

    def _set_access_token(self):
        """
        Sets the access token for your session.
        """
        authResponse = requests.post(self.ouath_url, data=self.data)
        if authResponse.status_code != 200:
            authResponse.raise_for_status()

        authJson = json.loads(authResponse.text)

        self.access_token = authJson["access_token"]
        self.expiration = datetime.fromtimestamp(int(authJson["expires_on"]))

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
