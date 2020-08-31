from abc import ABC
from abc import abstractmethod


class AtlasAuthBase(ABC):
    """
    The base class for authentication to your Apache Atlas server.
    """

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_authentication_headers(self, **kwargs):
        """
        Provide the authentication headers for HTTP requests.
        :return: The authorization headers.
        :rtype: dict(str, str)
        """
        raise NotImplementedError
