def apply_columnMapping_to_Process(atlas_entities):
    """
    Update the table processes to use the columnMapping attribute to
    represent column lineages in the Data Catalog UI.
    """
    # Find all processes
    procs_for_tables = []

    guids = {}
    # guid: {
    # type:(table/column/table_process/columnLineageProcess),
    # parent: guid
    # child: 
    # }

    for entity in atlas_entities:

        # Column Lineage Process
        if "query" in entity.relationshipAttributeDefs:
            # TODO: Make this more dynamic and not hard code query
            parent_guid = entity.relationshipAttributes["query"]["guid"]
            guid[parent_guid] = {
                "type":"column_lineage_process",
                "input_guid":next(iter(entity.attributes["inputs"]), None), # There may not be a first element
                "output_guid":entity.attributes["outputs"][0] # Always assuming there is an output
            }
        # Non column lineage process
        elif "inputs" in entity.attributes and "outputs" in entity.attributes:
            guids[entity.guid] = {
                "type":"table_process",
                "input_guid":next(iter(entity.attributes["inputs"]), None), # There may not be a first element
                "output_guid":entity.attributes["outputs"][0] # Always assuming there is an output
            }
            procs_for_tables.append(entity)

        else:
            guids[entity.guid] = {"name":entity.get_name()}

    for proc in procs_for_tables:
        input_table_name = guids.get(guids[proc.guid]["input_guid"], {}).get("name")
        output_table_name = guids.get(guids[proc.guid]["output_guid"], {}).get("name")
    # Extract the tables from input output
    # Find all columns that point to that table
    # Find the column lineages processes
    # TODO: MAJOR!

    return NotImplementedError


def child_type_from_relationship(relationship_name, atlas_typedefs, normalize=True):
    """
    Extract the child type of of a relationship attribute def 
    inside a type def.

    :param str relationship_name:
    :param list(dict) atlas_typedefs:
    :param bool normalize: If True, remove the array<X> reference and return
        only X.
    :return: The child type name of a relationship attribute.
    :rtype: str
    """
    output = None
    for typdedf in atlas_typedefs:
        for relationshipDef in typdedf["relationshipAttributeDefs"]:
            if relationshipDef.get("name", None) == relationship_name:
                output = relationshipDef.get("typeName")
                if normalize and output.startswith("array<") and output.endswith(">"):
                    # Assuming typename looks like array<{typename}>
                    output = output[6:-1]
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
    :return: The atlas entity that maches or None
    :rtype: Union(:class:`~pyapacheatlas.core.entity.AtlasEntity`, None)
    """
    output = None
    for entity in atlas_entities:
        if attribute in entity.attributes:
            if entity.attributes[attribute] == value:
                output = entity
                break        
    return output

def first_process_matching_io(input_name, output_name, atlas_entities):
    """
    Return the first entity in a list that contains the inputs and outputs.

    :param str inputs: The qualified name of an atlas entity.
    :param str outputs: The qualified name of an atlas entity.
    :param atlas_entities: The list of atlas entities to search over.
        :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :return: The atlas entity that maches or None
    :rtype: Union(:class:`~pyapacheatlas.core.entity.AtlasEntity`, None)
    """
    output_entity = None
    for entity in atlas_entities:
        input_matches = False
        output_matches = False
        if "inputs" in entity.attributes and "outputs" in entity.attributes:
            num_inputs = len(entity.attributes["inputs"])
            num_outputs = len(entity.attributes["outputs"])
            input_matches = ((
                (input_name is None) and (num_inputs == 0)) or
                ((input_name is not None) and (num_inputs >0) and 
                    (entity.attributes["inputs"][0]["qualifiedName"] == input_name))
            )
            output_matches = ((
                (output_name is None) and (num_outputs == 0)) or
                ((output_name is not None) and (num_outputs >0) and 
                    (entity.attributes["outputs"][0]["qualifiedName"] == output_name))
            )
        if input_matches and output_matches:
            output_entity = entity
    
    return output_entity


def from_process_lookup_col_lineage(process_name, existing_mapping, atlas_entities, atlas_typedefs):
    """
    Given a process name, find

    existing_mapping is expected to follow `{process:{column_lineage_type, process_type}}`

    :param str process_name: 
    :param dict(str,dict(str,str)) existing_mapping: 
        An existing mapping to act as a cache and speed up searching.
    :param atlas_entities: The list of atlas entities to search over.
        :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :param list(dict) atlas_typedefs: The list of type definitions to extract from.
    :return: The atlas entity that maches or None
    :rtype: Union(:class:`~pyapacheatlas.core.entity.AtlasEntity`, None)
    """
    column_lineage_type = None
    if process_name in existing_mapping:
        column_lineage_type = existing_mapping[process_name]["column_lineage_type"]
    else:
        target_entity = first_entity_matching_attribute("name", process_name, atlas_entities)
        if target_entity is not None:
            # TODO: Make "columnLineages" dynamic so that you can control which attribute you're searching for
            column_lineage_type = child_type_from_relationship("columnLineages", atlas_typedefs)
            existing_mapping[process_name] = {
                "column_lineage_type":column_lineage_type,
                "process_type":target_entity.typeName
            }
    
    return existing_mapping, column_lineage_type

def string_to_classification(string, sep=";"):
    """
    Converts a string of text into classifications.

    :param str string: The string that contains one or more classifications.
    :param str sep: The separator to split the `string` parameter on.
    :return: A list of AtlasClassification objects as dicts.
    :rtype: list(dict)
    """
    if string is None:
        return []
    # TODO: How do we bring in attributes if they're required?
    results = [{"typeName": s.strip(), "attributes":{}} for s in string.split(sep) if s.strip() != ""]
    return results
