from functools import wraps
import warnings


class AtlasException(BaseException):
    pass


def PurviewOnly(func):
    """
    Raise a runtime warning if you are using an AtlasClient (or non Purview)
    client. Intended to wrap specific client methods that are only available
    in Purview.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not args[0].is_purview:
            warnings.warn(
                "You're using a Purview only feature on a non-purview endpoint.",
                RuntimeWarning
            )
        return func(*args, **kwargs)
    return wrapper


def PurviewLimitation(func):
    """
    Raise a runtime warning if you are using a PurviewClient. Intended to wrap
    specific client methods that have limitations due to Purview.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if args[0].is_purview:
            warnings.warn(
                "You're using a feature that Purview does not implement fully.",
                RuntimeWarning
            )
        return func(*args, **kwargs)
    return wrapper


class GuidTracker():
    """
    Always grab the next available guid by either inrementing or decrementing.
    When defining an interconnected set of Atlas Entities, you use a
    negative integer to provide an entity with a temporary unique id.
    """

    def __init__(self, starting=-1000, direction="decrease"):
        """
        :param int starting: A negative integer to start your guid tracker on.
        :param str direction: Either increase or decrease. It controls
            whether you increment or decrement the guid.
        """
        _ALLOWED_DIRECTIONS = ["increase", "decrease"]

        if direction not in _ALLOWED_DIRECTIONS:
            raise NotImplementedError(
                "The direction of {} is not supported.  Only {}".format(
                    direction, _ALLOWED_DIRECTIONS))

        self._guid = starting
        self._direction = direction

    def _decide_next_guid(self):
        """
        Do the math to determine what the next guid would be but do not
        update the guid.

        :return: The next guid you would receive.
        :rtype: int
        """
        return self._guid + (-1 if self._direction == "decrease" else 1)

    def get_guid(self):
        """
        Retrieve the next unique guid and update the guid.

        :return: A "unique" integer guid for your atlas object.
        :rtype: int
        """
        self._guid = self._decide_next_guid()
        return self._guid

    def peek_next_guid(self):
        """
        Peek at the next guid without updating the guid.

        :return: The next guid you would receive.
        :rtype: int
        """
        return self._decide_next_guid()
