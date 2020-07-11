from datetime import datetime
import json
import requests

class OAuthMSFT():

    def __init__(self, tenant_id, client_id, client_secret):
        super().__init__()

        self.ouath_url = "https://login.microsoftonline.com/" + tenant_id + "/oauth2/token"
        self.data = {"resource": "https://management.core.windows.net/",
            "client_id": client_id,
            "grant_type": "client_credentials",
            "client_secret": client_secret}
        self.access_token = None
        self.expiration = datetime.now()

        
    def _set_access_token(self):
        authResponse = requests.post(self.ouath_url, data=self.data)
        if authResponse.status_code != 200:
            authResponse.raise_for_status()
        
        authJson = json.loads(authResponse.text)

        self.access_token = authJson["access_token"]
        self.expiration = datetime.fromtimestamp(int(authJson["expires_in"]))


    def get_headers(self):
        if self.expiration <= datetime.now():
            self._set_access_token()

        return {
            "Authorization": "Bearer " + self.access_token,
            "Content-Type": "application/json"
        }