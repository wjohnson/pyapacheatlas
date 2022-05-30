from functools import wraps
import json
from json import JSONDecodeError
import re
import warnings

import requests


class AtlasBaseClient():
    def __init__(self, **kwargs):
        if "requests_args" in kwargs:
            self._requests_args = kwargs["requests_args"]
        else:
            self._requests_args = {}
        super().__init__()
    
    @staticmethod
    def _parse_requests_args(**kwargs):
        output = dict()
        keys = [k for k in kwargs.keys() if k.startswith("requests_")]
        for k in keys:
            output[k.split("_", 1)[1]] = kwargs.pop(k)
        return output

    def _handle_response(self, resp):
        """
        Safely handle an Atlas Response and return the results if valid.

        :param Response resp: The response from the request method.
        :return: A dict containing the results.
        :rtype: dict
        """

        try:
            results = json.loads(resp.text)
            resp.raise_for_status()
        except JSONDecodeError:
            raise ValueError("Error in parsing: {}".format(resp.text))
        except requests.RequestException as e:
            if "errorCode" in results:
                raise AtlasException(resp.text)
            else:
                raise requests.RequestException(resp.text)

        return results


class AtlasException(BaseException):
    pass


class AtlasUnInit():
    """
    Represents a value that has not been initialized
    and will not be included in json body.
    """

    def __bool__(self):
        return False


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
        :rtype: str
        """
        self._guid = self._decide_next_guid()
        return str(self._guid)

    def peek_next_guid(self):
        """
        Peek at the next guid without updating the guid.

        :return: The next guid you would receive.
        :rtype: str
        """
        return str(self._decide_next_guid())


def _find_relationship_guids(entity):
    # TODO: Handle arrays of attributes
    """
    Extract all of the guids from the relationship attributes
    for a given JSON AtlasEntity.

    :param dict entity: An AtlasEntity as a JSON dict
    :return: A set of guids.
    :rtype: list(Union(str, int))
    """
    output = set()
    if "relationshipAttributes" in entity:
        ra = entity["relationshipAttributes"]
        for attrib in ra:
            if "guid" in ra[attrib]:
                output.add(ra[attrib]["guid"])

    return list(output)


def batch_dependent_entities(entities, batch_size=1000):
    """
    Take a list of entities and organize them to batches of max `batch_size`.

    This algorithm handles uploading multiple entities that are dependent on
    each other. For example, if A depends on B and B depends on C then the
    three entities will guaranteed be in the same batch. 

    Dependencies can be specified in either direction. For example a table
    may not have any relationship attribute dependencies. However, several
    columns may point to the given table. This will be handled by this
    function.

    :param list(dict) entities: A list of AtlasEntities to be uploaded as dicts
    :param int batch_size: 
    :return:
        A list of lists that organize the entities into batches of max
        `batch_size` and are in "most independent" to "least independent"
        meaning the batches with more dependencies between its entities
        will be at the end of the list of lists.
    :rtype: list( list(dict) )
    """
    index = {}
    original_index = {}

    sets = []

    print(f"Number of entities: {len(entities)}")

    for idx, entity in enumerate(entities):
        candidate_sets = []
        entity_id = entity["guid"]
        original_index[entity_id] = idx
        entity_pointsTo = _find_relationship_guids(entity)
        # Does the related entity match the negative
        # number guid pattern? NO? Remove it from index
        # This will still error out on upload but not mess
        # with sorting / marking it as a dependency within
        # the upload
        for related_entity in entity_pointsTo:
            if not re.match(r"-\d*$", str(related_entity)):
                entity_pointsTo.pop(
                    entity_pointsTo.index(related_entity)
                )
        # Do you have pointers
        # No
        if len(entity_pointsTo) == 0:
            # Already Seen?
            #### Yes: Continue
            if entity_id in index:
                continue
            # No: Independent Set; Mark as Seen
            else:
                # Independent, will update below
                pass
        # Yes I do have pointers
        else:
            # Have I seen the main entity before?
            if entity_id in index:
                candidate_sets.append(index[entity_id])

            # for each sub entity check if I've seen it before
            for subentityId in entity_pointsTo:
                # Already Seen?
                # Yes: Find set it belongs to
                if subentityId in index:
                    candidate_sets.append(index[subentityId])
                # No: Independent set
                else:
                    pass

        entity_set = set([entity_id] + entity_pointsTo)
        # They're all independent
        if len(candidate_sets) == 0:
            sets.append(entity_set)
            new_set_position = len(sets) - 1
            for each in entity_set:
                index[each] = new_set_position
        # There is something seen before
        # There's only one option
        elif len(candidate_sets) == 1:
            candidate_location = candidate_sets[0]
            sets[candidate_location] = sets[candidate_location].union(
                entity_set)
            for each in entity_set:
                index[each] = new_set_position

        # There are multiple candidate sets where this entity
        # points to known entities that are already in a set
        # we have to merge all the candidate sets together
        else:
            combo_entity_set = entity_set
            largest_candidate_index = None
            largest_candidate_size = 0
            largest_candidate_set = set()

            # To reduce the number of updates to the index
            # Iterate over all of the candidate sets
            # Identify the index position of the largest candidate set
            # Hopefully saving a few thousands updates in the worst case?
            # Build up one master set that will be the new group
            # (from the current entity) and assigned to the largest
            # candidate set's index position.
            for candidate_index in candidate_sets:
                candidate_set = sets[candidate_index]
                if len(candidate_set) > largest_candidate_size:
                    largest_candidate_size = len(candidate_set)
                    largest_candidate_index = candidate_index
                    largest_candidate_set = candidate_set

                combo_entity_set = combo_entity_set.union(candidate_set)

            # Update the index for the entities that are NOT in
            # the largest candidate set
            entities_to_update = combo_entity_set.difference(
                largest_candidate_set)
            for entity_id in entities_to_update:
                index[entity_id] = largest_candidate_index

            # Now that the combined entities are pointing to the updated
            # / largest set, I can remove the actual sets that my
            # remaining candidate sets point to.
            # I do NOT want to delete the largest set so I have to remove
            # it from candidate_sets first
            largest_candidate_index_in_candidate_sets = candidate_sets.index(
                largest_candidate_index)
            candidate_sets.pop(largest_candidate_index_in_candidate_sets)

            # Update the set that was deemed to be the largest of the
            # candidates with the even LARGER combination of entities
            sets[largest_candidate_index] = combo_entity_set

            # Now I can remove all of the "physical" sets that were
            # referenced in our candidate_sets (excluding  the largest one)
            # because all of the entities in those sets are now under the
            # largest candidate set
            for removed_candidate_index in candidate_sets:
                sets[removed_candidate_index] = None

    # Sort the list from smallest to largest
    ordered_sets = sorted([s for s in sets if s is not None],
                          key=lambda s: len(s), reverse=False)

    maximized_batches = []

    # Greedily maximize
    while(len(ordered_sets) > 0):
        # Take the first (presumably the smallest) and start building it up
        principal_set = ordered_sets.pop(0)
        # We then need to have a list of the sets that will be deleted / merged
        sets_to_delete = []

        # If the set is SO large blow up
        if len(principal_set) > batch_size:
            raise ValueError("You have a group of dependent entities that exceed your max batch size. Total dependency group size: {}".format(
                len(principal_set)))
        # If the set is equal to the batch size, add it to the maximized batch
        # no need to process further because we don't need to look at the next
        # largest set to merge
        elif len(principal_set) == batch_size:
            maximized_batches.append(principal_set)
            continue

        # Build up the principal set from the next largest set
        for smaller_index, smaller_set in enumerate(ordered_sets):
            principal_set_len = len(principal_set)
            if principal_set_len + len(smaller_set) > batch_size:
                pass
            else:
                principal_set = principal_set.union(smaller_set)
                sets_to_delete.append(smaller_index)

        # Iterated over all of the other sets so now append this principal set can be inserted
        maximized_batches.append(principal_set)

        # remove any record set marked for deletion
        # Make sure you delete the latest record first
        for set_to_delete in sorted(sets_to_delete, reverse=True):
            ordered_sets.pop(set_to_delete)

    output_batches = []
    # I've been working with pointers and guids at this point now I have to
    # actually output the entities as lists of lists
    # For every batch that has been maximized to the batch_size, take the
    # pointer and use it to find the actual entity in the original index
    # which gives a pointer to the index of the entities list that was
    # originally passed in
    for inner_batch in maximized_batches:
        sub_output_batch = []
        for entity_index_pointer in inner_batch:
            pointer = original_index[entity_index_pointer]
            sub_output_batch.append(entities[pointer])
        output_batches.append(sub_output_batch)

    return output_batches

def _handle_response(resp):
    """
    Safely handle an Atlas Response and return the results if valid.

    :param Response resp: The response from the request method.
    :return: A dict containing the results.
    :rtype: dict
    """

    try:
        results = json.loads(resp.text)
        resp.raise_for_status()
    except JSONDecodeError:
        raise ValueError("Error in parsing: {}".format(resp.text))
    except requests.RequestException as e:
        if "errorCode" in results:
            raise AtlasException(resp.text)
        else:
            raise requests.RequestException(resp.text)

    return results
