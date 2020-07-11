class GuidTracker():

    def __init__(self, starting, direction="decrease"):
        _ALLOWED_DIRECTIONS = ["increase", "decrease"]

        if direction not in _ALLOWED_DIRECTIONS:
            raise NotImplementedError("The direction of {} is not supported.  Only {}".format(direction, _ALLOWED_DIRECTIONS))

        self._guid = starting
        self._direction = direction

    def _decide_next_guid(self):
        return self._guid + (-1 if self._direction == "decrease" else 1)

    def get_guid(self):
        self._guid = self._decide_next_guid()
        return self._guid
    
    def peek_next_guid(self):
        return self._decide_next_guid()

