import base64

from .base import AtlasAuthBase


class BasicAuthentication(AtlasAuthBase):
    """
    Authenticates using basic authentication.  Primarily used for testing
    on local
    """

    def __init__(self, username, password):
        """
        :param str username: The basic auth username.
        :param str username: The basic auth password.
        """
        super().__init__()
        self._username = username
        self._password = password

    def get_authentication_headers(self):
        """
        Provide the authentication headers for HTTP requests.
        :return: The authorization headers.
        :rtype: dict(str, str)
        """
        byte_user_pass = bytes("{u}:{pw}".format(
            u=self._username, pw=self._password), "utf-8")
        b64_str_userpass = base64.standard_b64encode(
            byte_user_pass).decode("utf-8")
        return {"Authorization": "Basic {}".format(b64_str_userpass)}
