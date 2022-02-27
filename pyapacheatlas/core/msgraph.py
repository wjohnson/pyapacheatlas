import json
from json import JSONDecodeError
import requests


class MsGraphException(BaseException):
    pass


class MsGraphClient():

    def __init__(self, authentication, **kwargs):
        super().__init__()
        self.authentication = authentication
        self._requests_args = kwargs.get("requests_args", {})

    def upn_to_id(self, userPrincipalName, api_version="v1.0"):
        """
        Based on user principal name, look up the user in Azure Active directory.

        :param str userPrincipalName: The user principal name of the user.
        :return:
            The AAD object id of the user principal name.
        :rtype: str
        """
        graph_endpoint = f"https://graph.microsoft.com/{api_version}/users/{userPrincipalName}"

        getUser = requests.get(
            graph_endpoint,
            headers=self.authentication.get_graph_authentication_headers(),
            **self._requests_args
        )

        try:
            results = json.loads(getUser.text)["id"]
            getUser.raise_for_status()
        except JSONDecodeError:
            raise ValueError(
                f"For UPN {userPrincipalName}: Error in parsing: {getUser.text}")
        except requests.RequestException as e:
            raise requests.RequestException(
                f"For UPN {userPrincipalName}: Error in parsing: {getUser.text}")
        except KeyError:
            raise KeyError(
                f"For UPN {userPrincipalName}: Response did not include an id field:"+json.dumps(results))

        return results

    def email_to_id(self, email, api_version="v1.0"):
        """
        Based on email address, look up the user in Azure Active directory.
        It's set to exact match on the mail field of the graph user response.

        :param str email: The email address of the user.
        :return: The AAD object id of the user principal name.
        :rtype: str
        """
        graph_endpoint = f"https://graph.microsoft.com/{api_version}/users?$filter=mail eq '{email}'"

        getUser = requests.get(
            graph_endpoint,
            headers=self.authentication.get_graph_authentication_headers(),
            **self._requests_args
        )

        try:
            graph_response = json.loads(getUser.text)
            getUser.raise_for_status()

            if len(graph_response["value"]) == 0:
                raise MsGraphException(
                    f"The response from MS Graph for '{email}' contained zero results.")
            results = graph_response["value"][0]["id"]
        except JSONDecodeError:
            raise ValueError(
                f"For email {email}: Error in parsing response: {getUser.text}")
        except requests.RequestException as e:
            raise requests.RequestException(
                f"For email {email}: Error in parsing response: {getUser.text}")
        except KeyError:
            raise KeyError(
                f"For email {email}: Response did not include a value or id field:"+json.dumps(graph_response))

        return results
