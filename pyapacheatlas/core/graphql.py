from .. import __version__
import json
from typing import Union, List
from json import JSONDecodeError
import requests
from .util import AtlasResponse


class GraphQLException(BaseException):
    pass


class GraphQLClient():
    """
    Implements the GraphQL connection in Microsoft Purview.

    Do not instantiate this directly, instead, it is used by PurviewClient.
    This is not available to that AtlasClient.
    """

    def __init__(self, endpoint_url, authentication, **kwargs):
        super().__init__()
        self.endpoint_url = endpoint_url
        self.authentication = authentication
        self._requests_args = kwargs.get("requests_args", {})
        self._USER_AGENT = {"User-Agent": "pyapacheatlas/{0} {1}".format(
            __version__, requests.utils.default_headers().get("User-Agent"))}
    
    def _generate_request_headers(self, include: dict = {}, exclude: List[str] = []):
        auth = {} if self.authentication is None else self.authentication.get_authentication_headers()

        if include:
            auth.update(include)
        if exclude:
            for key in exclude:
                if key in auth:
                    auth.pop(key)
        return dict(**auth, **self._USER_AGENT)
    
    def _post_http(self, url: str, params: dict = None,
                   json: Union[list, dict] = None, files: dict = None,
                   **kwargs) -> AtlasResponse:
        """
        :kwargs dict headers_include:Additional headers to include.
        :kwargs List[str] headers_include:Additional headers to include.
        """
        extra_args = {}
        if json:
            extra_args["json"] = json
        if params:
            extra_args["params"] = params
        if files:
            extra_args["files"] = files
        response_args = {}
        if "responseNotJson" in kwargs:
            response_args["responseNotJson"] = kwargs["responseNotJson"]
        return AtlasResponse(
            requests.post(
                url,
                headers=self._generate_request_headers(kwargs.get(
                    "headers_include"), kwargs.get("headers_exclude")),
                **extra_args,
                **self._requests_args
            ),
            **response_args
        )
    
    def query(self, query:str):
        """
        Execute a GraphQL query on the Purview Datamap.

        :param str query:

        :return: The GraphQL response object
        :rtype: dict

        [Reference](https://learn.microsoft.com/en-us/purview/tutorial-graphql-api)
        """
        graphQL_response = self._post_http(
            self.endpoint_url,
            json={"query":query}
        )
        return graphQL_response.body
