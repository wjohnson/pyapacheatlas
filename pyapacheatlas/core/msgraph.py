import json
from json import JSONDecodeError
import requests

class MsGraphClient():

    def __init__(self, authentication):
        super().__init__()
        self.authentication = authentication

    def upn_to_id(self, userPrincipalName, api_version="v1.0"):
        """
        Based on user principal name, look up the user in Azure Active directory.

        :param str userPrincipalName:
        :return:
            The results of the microsoft graph user lookup.
        :rtype: dict
        """
        graph_endpoint = f"https://graph.microsoft.com/{api_version}/users/{userPrincipalName}"

        getUser = requests.get(
            graph_endpoint,
            headers=self.authentication.get_graph_authentication_headers()
        )

        try:
            results = json.loads(getUser.text)["id"]
            getUser.raise_for_status()
        except JSONDecodeError:
            raise ValueError("Error in parsing: {}".format(getUser.text))
        except requests.RequestException as e:
            raise requests.RequestException(getUser.text)
        except KeyError:
            raise KeyError("Response did not include an id field:"+json.dumps(results))

        return results
