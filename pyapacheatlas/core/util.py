class AtlasException(BaseException):
    pass

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
