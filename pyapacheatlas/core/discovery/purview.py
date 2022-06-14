import requests

from ..util import AtlasBaseClient


class PurviewDiscoveryClient(AtlasBaseClient):
    def __init__(self, endpoint_url, authentication, **kwargs):
        super().__init__(**kwargs)
        self.endpoint_url = endpoint_url
        self.authentication = authentication

    def autocomplete(
        self, keywords=None, filter=None, api_version="2021-05-01-preview", **kwargs
    ):
        """
        Execute an autocomplete search request on Azure Purview's
        `/catalog/api/search/autocomplete` endpoint.

        :param dict body:
            An OPTIONAL fully formed json body. If provided, all other params
            will be ignored except api-version.
        :param str keywords:
            The keywords applied to all fields that support autocomplete
            operation. It must be at least 1 character, and no more than 100
            characters.
        :param dict filter:
            A json object that includes and, not, or conditions and ultimately
            a dict that contains attributeName, operator, and attributeValue.
        :param int limit: The number of search results to return.
        :param str api_version: The Purview API version to use.
        :return: Autocomplete Search results with a value field.
        :rtype: dict
        """
        req_body = {}
        if "body" in kwargs:
            req_body.update(kwargs["body"])
        elif keywords:
            req_body = {"keywords": keywords}
            if filter:
                req_body.update({"filter": filter})
            # Additional properties
            for prop in ["limit"]:
                if prop in kwargs:
                    req_body[prop] = kwargs[prop]
        else:
            raise RuntimeError(
                "Failed to execute autocomplete query. Please provide either a keywords or a well formed JSON body."
            )

        atlas_endpoint = self.endpoint_url + "/search/autocomplete"
        postResult = requests.post(
            atlas_endpoint,
            json=req_body,
            params={"api-version": api_version},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResult)

        return results

    # TODO: Having auth issues?
    def browse(self, entityType=None, api_version="2021-05-01-preview", **kwargs):
        """
        Execute a browse search for Purview based on the entity against the
        `/catalog/api/browse endpoint`.

        :param str entityType:
            The entity type to browse as the root level entry point. This must
            be a valid Purview built-in or custom type.
        :param str path: The path to browse the next level child entities.
        :param int limit: The number of search results to return.
        :param int offset: The number of search results to skip.
        :param str api_version: The Purview API version to use.
        :return: Search query results with @search.count and value fields.
        :rtype: dict
        """
        req_body = {}
        if "body" in kwargs:
            req_body.update(kwargs["body"])
        elif entityType:
            req_body = {"entityType": entityType}
            # Additional properties
            for prop in ["limit", "offset"]:
                if prop in kwargs:
                    req_body[prop] = kwargs[prop]
        else:
            RuntimeError(
                "Failed to execute browse query. Please provide either an entityType or a well formed JSON body."
            )

        atlas_endpoint = self.endpoint_url + "/browse"
        # TODO: Implement paging with offset and limit
        postResult = requests.post(
            atlas_endpoint,
            json=req_body,
            params={"api-version": api_version},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResult)

        return results

    def query(
        self,
        keywords=None,
        filter=None,
        facets=None,
        taxonomySetting=None,
        api_version="2021-05-01-preview",
        **kwargs
    ):
        """
        Execute a search query against Azure Purview's `/catalog/api/search/query`
        endpoint.

        :param dict body:
            An optional fully formed json body. If provided, all other params
            will be ignored except api-version.
        :param str keywords:
            The keyword to search. You can use None or '*' for wildcard, or
            a string to search.
        :param dict filter:
            A json object that includes and, not, or conditions and ultimately
            a dict that contains attributeName, operator, and attributeValue.
        :param dict facets:
            The kind of aggregate count you want to retrieve. Should be a dict
            that contains fields: count, facet, and sort.
        :param dict taxonomySetting: Undocumented.
        :param int limit: The number of search results to return.
        :param int offset: The number of search results to skip.
        :param str api_version: The Purview API version to use.
        :return: Search query results with @search.count and value fields.
        :rtype: dict
        """
        req_body = {}
        if "body" in kwargs:
            req_body.update(kwargs["body"])
        elif keywords or filter:
            req_body = {
                "keywords": keywords,
                "filter": filter,
            }
            if facets:
                req_body.update({"facets": facets})
            if taxonomySetting:
                req_body.update({"taxonomySetting": taxonomySetting})
            # Additional properties
            for prop in ["limit", "offset"]:
                if prop in kwargs:
                    req_body[prop] = kwargs[prop]

        else:
            raise RuntimeError(
                "Failed to execute search query. Please provide either a keyword or a well formed JSON body."
            )

        atlas_endpoint = self.endpoint_url + "/search/query"
        # TODO: Implement paging with offset and limit
        postResult = requests.post(
            atlas_endpoint,
            json=req_body,
            params={"api-version": api_version},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResult)

        return results

    def suggest(
        self, keywords=None, filter=None, api_version="2021-05-01-preview", **kwargs
    ):
        """
        Execute a sugest search request on Azure Purview's
        `/catalog/api/search/suggest` endpoint.

        :param dict body:
            An optional fully formed json body. If provided, all other params
            will be ignored except api-version.
        :param str keywords:
            The keywords applied to all fields that support autocomplete
            operation. It must be at least 1 character, and no more than 100
            characters.
        :param dict filter:
            A json object that includes and, not, or conditions and ultimately
            a dict that contains attributeName, operator, and attributeValue.
        :param int limit: The number of search results to return.
        :param str api_version: The Purview API version to use.
        :return: Suggest Search results with a value field.
        :rtype: dict
        """
        req_body = {}
        if "body" in kwargs:
            req_body.update(kwargs["body"])
        elif keywords:
            req_body = {"keywords": keywords}
            if filter:
                req_body.update({"filter": filter})
            # Additional properties
            for prop in ["limit"]:
                if prop in kwargs:
                    req_body[prop] = kwargs[prop]
        else:
            raise RuntimeError(
                "Failed to execute suggest query. Please provide either a keywords or a well formed JSON body."
            )

        atlas_endpoint = self.endpoint_url + "/search/suggest"
        postResult = requests.post(
            atlas_endpoint,
            json=req_body,
            params={"api-version": api_version},
            headers=self.authentication.get_authentication_headers(),
            **self._requests_args
        )

        results = self._handle_response(postResult)

        return results

    def _search_generator(self, **kwargs):
        """
        Generator to page through the search query results.
        """
        offset = kwargs["starting_offset"] if "starting_offset" in kwargs else 0

        while True:
            results = self.query(
                keywords=kwargs.get("keywords"),
                filter=kwargs.get("filter"),
                facets=kwargs.get("facets"),
                taxonomySetting=kwargs.get("taxonomySetting"),
                api_version=kwargs["api_version"],
                limit=kwargs.get("limit", 1000),
                offset=offset,
                **self._requests_args
            )

            return_values = results["value"]
            return_count = len(return_values)

            if return_count == 0:
                return

            offset = offset + return_count

            # if the new offset is larger than the total result count, we'll just return to avoid an additional call to the service.
            # This can increase the performance when the total call number is small
            if offset > results['@search.count']:
                return

            for sub_result in return_values:
                try:
                    yield sub_result
                except StopIteration:
                    return

    def search_entities(
        self,
        query,
        limit=50,
        search_filter=None,
        starting_offset=0,
        api_version="2021-05-01-preview",
        **kwargs
    ):
        """
        Search entities based on a query and automaticall handles limits and
        offsets to page through results.

        The limit provides how many records are returned in each batch with a
        maximum of 1,000 entries per page.

        :param str query: The search query to be executed.
        :param int limit:
            A non-zero integer representing how many entities to
            return for each page of the search results.
        :param dict search_filter:
            A json object that includes and, not, or conditions and ultimately
            a dict that contains attributeName, operator, and attributeValue.
        :param dict facets:
            The kind of aggregate count you want to retrieve. Should be a dict
            that contains fields: count, facet, and sort.
        :param dict taxonomySetting: Undocumented.
        :param int offset: The number of search results to skip.
        :param str api_version: The Purview API version to use.

        Kwargs:
            :param dict body: An optional fully formed json body. If provided
            query/keywords, limit, search_filter/filter, and
            starting_offset/offset will be updated using the values found
            in the body dictionary. Any additional keys provided in `body`
            will be passed along as additional kwargs.

        :return: The results of your search as a generator.
        :rtype: Iterator(dict)
        """
        if "body" in kwargs:
            req_body = kwargs.pop("body")
            if "keywords" in req_body:
                query = req_body.pop("keywords")
            if "limit" in req_body:
                limit = req_body.pop("limit")
            if "filter" in req_body:
                search_filter = req_body.pop("filter")
            if "offset" in req_body:
                starting_offset = req_body.pop("offset")
            kwargs.update(req_body)
        if limit > 1000 or limit < 1:
            raise ValueError(
                "The limit parameter must be non-zero and less than 1,000."
            )

        search_generator = self._search_generator(
            keywords=query,
            filter=search_filter,
            limit=limit,
            starting_offset=starting_offset,
            api_version=api_version,
            **kwargs
        )

        return search_generator
