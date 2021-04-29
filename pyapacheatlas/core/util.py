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

            for candidate_index in candidate_sets:
                candidate_set = sets[candidate_index]
                if len(candidate_set) > largest_candidate_size:
                    largest_candidate_size = len(candidate_set)
                    largest_candidate_index = candidate_index
                    largest_candidate_set = candidate_set

                combo_entity_set = combo_entity_set.union(candidate_set)

            # Update the index for these entities
            entities_to_update = combo_entity_set.difference(
                largest_candidate_set)
            for entity_id in entities_to_update:
                index[entity_id] = largest_candidate_index

            largest_candidate_index_in_candidate_sets = candidate_sets.index(largest_candidate_index)
            candidate_sets.pop(largest_candidate_index_in_candidate_sets)

            sets[largest_candidate_index] = combo_entity_set

            for removed_candidate_index in candidate_sets:
                sets[removed_candidate_index] = None
    print("Printing idx, original index, index, sets")
    #print(idx, original_index, index, sets, sep="\n")
    print("Finished out")

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
    for inner_batch in maximized_batches:
        sub_output_batch = []
        for entity_index_pointer in inner_batch:
            pointer = original_index[entity_index_pointer]
            sub_output_batch.append(entities[pointer])
        output_batches.append(sub_output_batch)
    
    print([len(x) for x in output_batches])

    return output_batches
