from warnings import warn
from ...core import AtlasEntity
from ...core import GuidTracker
from ...readers.util import string_to_classification


def to_bulkEntities(json_rows, starting_guid=-1000):
    """
    Create an AtlasTypeDef consisting of entities and their attributes for the given json_rows.

    :param list(dict(str,str)) json_rows:
        A list of dicts containing at least `Entity TypeName` and `name`
        that represents the metadata for a given entity type's attributeDefs.
        Extra metadata will be ignored.
    :return: An AtlasTypeDef with entityDefs for the provided rows.
    :rtype: dict(str, list(dict))
    """
    # For each row,
    # Extract the
    # Extract any additional attributes
    req_attribs = ["typeName", "name", "qualifiedName", "classifications"]
    gt = GuidTracker(starting_guid)
    output = {"entities": []}
    for row in json_rows:
        # Remove any cell with a None / Null attribute
        # Remove the required attributes so they're not double dipping.
        custom_attributes = {
            k: v for k, v in row.items()
            if k not in req_attribs and v is not None
        }
        entity = AtlasEntity(
            name=row["name"],
            typeName=row["typeName"],
            qualified_name=row["qualifiedName"],
            guid=gt.get_guid(),
            attributes=custom_attributes,
            classifications=string_to_classification(row["classifications"])
        ).to_json()
        output["entities"].append(entity)
    return output
