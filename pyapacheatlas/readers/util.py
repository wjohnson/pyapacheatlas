from ..core.entity import AtlasUnInit

def string_to_classification(string, sep=";"):
    """
    Converts a string of text into classifications.

    :param str string: The string that contains one or more classifications.
    :param str sep: The separator to split the `string` parameter on.
    :return: A list of AtlasClassification objects as dicts.
    :rtype: list(dict)
    """
    if string is None:
        return AtlasUnInit()
    # TODO: How do we bring in attributes if they're required?
    # Defaulting to NOT propagate the classification downstream.
    # Advanced users may decide to parse the classifications and update the
    # propagation themselves.
    results = [{"typeName": s.strip(), "attributes": {}, "propagate": False}
               for s in string.split(sep) if s.strip() != ""]
    return results


def columns_matching_pattern(row, starts_with, does_not_match=[]):
    """
    Takes in a json "row" and filters the keys to match the `starts_with`
    parameter.  In addition, it will remove any match that is included
    in the `does_not_match` parameter.

    :param dict row: A dictionary with string keys to be filtered.
    :param str starts_with:
        The required substring that all filtered results must start with.
    :param list(str) does_not_match:
        A list of key values that should be omitted from the results.
    :return: A dictionary that contains only the filtered results.
    :rtype: dict
    """
    candidates = {k: v for k, v in row.items() if str(
        k).startswith(starts_with)}
    for bad_key in does_not_match:
        if bad_key in candidates:
            candidates.pop(bad_key)
    candidates = {k[len(starts_with):].strip(): v for k,
                  v in candidates.items()}

    return candidates


def first_relationship_that_matches(end_def, end_def_type, end_def_name, relationship_typedefs):
    """
    Find the first relationship type that matches the end_def number, type
    and name from the provided typedefs.

    :param str end_def: Either 'endDef1' or 'endDef2'
    :param str end_def_type: The type within the end_def.
    :param str end_def_name:
        The name of the relationship attribute applied to the end def's entity.
        (e.g. columns, table, columnLineages, query)
    :param list(dict) relationship_typedefs:
        A list of dictionaries that follow the relationship type defs.
    :raises ValueError:
        An relationship dict was not found in the provided typedefs.
    :return: The matching relationship type definition.
    :rtype: dict
    """
    output = None
    for typedef in relationship_typedefs:
        if ((end_def in typedef) and
            (typedef[end_def]["type"] == end_def_type) and
                (typedef[end_def]["name"] == end_def_name)):
            output = typedef

    if output is None:
        raise ValueError(
            "Unable to find a relationship type that matches: {endDef} "
            "with type {end_def_type} and the name {end_def_name} from "
            "the {num_defs} provided."
            .format(
                endDef=end_def, end_def_type=end_def_type,
                end_def_name=end_def_name, num_defs=len(relationship_typedefs)
            )
        )

    return output


def first_entity_matching_attribute(attribute, value, atlas_entities):
    """
    Return the first entity in a list that matches the passed in attribute
    and value.

    :param str attribute: The name of the attribute to search on each
        atlas entity.
    :param str value: The value of the attribute to search on each
        atlas entity.
    :param atlas_entities: The list of atlas entities to search over.
    :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :raises ValueError:
        A matching entity was not found in the provided entities.
    :return: The atlas entity that maches the attribute and value.
    :rtype: :class:`~pyapacheatlas.core.entity.AtlasEntity`
    """
    output = None
    for entity in atlas_entities:
        if attribute in entity.attributes:
            if entity.attributes[attribute] == value:
                output = entity
                break
    if output is None:
        raise ValueError(
            "Unable to find an entity that matches the value of {value} in "
            "an attribute of {attribute} from the {num_entities} provided."
            .format(
                value=value, attribute=attribute,
                num_entities=len(atlas_entities)
            )
        )
    return output


def first_process_containing_io(input_name, output_name, atlas_entities):
    """
    Return the first entity in a list that contains the inputs and outputs.
    If input_name and output_name are the only or one of the many inputs and
    outputs (respectively), it will count as a match.

    :param str inputs:
        The qualified name of an atlas entity or a '*' wildcard
        that matches to any input (empty list or filled in values)
    :param str outputs: The qualified name of an atlas entity.
    :param atlas_entities: The list of atlas entities to search over.
    :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :raises ValueError:
        A matching entity was not found in the provided entities.
    :return: The atlas entity that maches.
    :rtype: :class:`~pyapacheatlas.core.entity.AtlasEntity`
    """
    output_entity = None
    for entity in atlas_entities:
        input_matches = False
        output_matches = False
        if "inputs" in entity.attributes and "outputs" in entity.attributes:
            num_inputs = len(entity.attributes["inputs"])
            num_outputs = len(entity.attributes["outputs"])
            input_matches = ((input_name == "*") or  # Wildcard
                             ((input_name is None) and (num_inputs == 0)) or
                             ((input_name is not None) and (num_inputs > 0) and
                              (any([e["qualifiedName"] ==
                                    input_name for e in entity.inputs ]))
                              )
                             )
            output_matches = (
                ((output_name is None) and (num_outputs == 0)) or
                ((output_name is not None) and (num_outputs > 0) and
                    (any([e["qualifiedName"] == output_name for e in entity.outputs ]))
                 )
            )
        if input_matches and output_matches:
            output_entity = entity

    if output_entity is None:
        num_entities = len(atlas_entities)
        raise ValueError(
            "Unable to find a process that includes input "
            f"qualified names: {input_name} and output "
            f"qualified names: {output_name} from the "
            f"{num_entities} provided."
            .format(
                input_name=input_name, output_name=output_name,
                num_entities=num_entities
            )
        )

    return output_entity


def from_process_lookup_col_lineage(process_name, atlas_entities, relationship_typedefs):
    """
    Given a process name, find the first entity that matches that process name.
    Given that process entity, find the first relationship that contains that
    process type as an endDef2.

    :param str process_name: The name of the process that you want to find.
    :param atlas_entities: The list of atlas entities to search over.
    :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :param list(dict) relationship_typedefs:
        The list of relationship type definitions to extract from.
    :raises ValueError:
        A matching entity or matching relationship type was not found in
        the provided entities or type def.
    :return: The endDef1 type from the discovered process relationship type.
    :rtype: str
    """
    target_entity = first_entity_matching_attribute(
        "name", process_name, atlas_entities)
    # TODO: Make "columnLineages" dynamic so that you can control which
    # attribute you're searching for

    lineage_relationship = first_relationship_that_matches(
        end_def="endDef2",
        end_def_type=target_entity.typeName,
        end_def_name="columnLineages",
        relationship_typedefs=relationship_typedefs
    )

    column_lineage_type = lineage_relationship["endDef1"]["type"]

    return column_lineage_type


def _make_col_qual_name(col_name, parent_table_name):
    """
    Generate a standardized qualified name for column entities.

    :param str col_name: The column name.
    :param str parent_table_name: The parent table name.

    :return: The qualified name for the column.
    :rtype: str
    """
    return f"{parent_table_name}#{col_name}"
