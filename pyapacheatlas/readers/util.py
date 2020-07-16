def apply_columnMapping_to_Process(atlas_entities, table_process, column_lineage_process):
    # Find all processes
    procs_for_tables = []

    guids = {}
    # guid: {
    # type:(table/column/table_process/columnLineageProcess),
    # parent: guid
    # child: 
    # }

    lineage_tree = {}
    # Table Process
    ## Input Table | Output Table
    ### C1 | C2    | C3 | C4
    ## Lineage
    ### C1 -> C3 | C2 -> C4

    for entity in atlas_entities:

        # Column Lineage Process
        if "query" in entity.relationshipAttributeDefs:
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

    return NotImplementedError


def child_type_from_relationship(entity_type, relationship_name, atlas_typedefs, normalize=True):
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
    output = None
    for entity in atlas_entities:
        if attribute in entity.attributes:
            if entity.attributes[attribute] == value:
                output = entity
                break        
    return output

def first_process_matching_io(input_name, output_name, atlas_entities):
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
        

def from_tablename_lookup_col(table_name, existing_mapping, atlas_entities, atlas_typedefs):
    if table_name in existing_mapping:
        column_type = existing_mapping[table_name]["column_type"]
    else:
        target_table = first_entity_matching_attribute("name", table_name, atlas_entities)
        # TODO: Make "column" dynamic so that you can control which attribute you're searching for
        column_type = child_type_from_relationship(target_table.typeName, "columns", atlas_typedefs)
        existing_mapping[table_name] = {
            "column_type": column_type,
            "table_type": target_table.typeName
        }
    
    return existing_mapping, column_type

def from_process_lookup_col_lineage(process_name, existing_mapping, atlas_entities, atlas_typedefs):
    column_lineage_type = None
    if process_name in existing_mapping:
        column_lineage_type = existing_mapping[process_name]["column_lineage_type"]
    else:
        target_entity = first_entity_matching_attribute("name", process_name, atlas_entities)
        if target_entity is not None:
            # TODO: Make "columnLineages" dynamic so that you can control which attribute you're searching for
            column_lineage_type = child_type_from_relationship(target_entity.typeName, "columnLineages", atlas_typedefs)
            existing_mapping[process_name] = {
                "column_lineage_type":column_lineage_type,
                "process_type":target_entity.typeName
            }
    
    return existing_mapping, column_lineage_type

def string_to_classification(string, sep=";"):
    if string is None:
        return []
    # TODO: How do we bring in attributes if they're required?
    results = [{"typeName": s.strip(), "attributes":{}} for s in string.split(sep) if s.strip() != ""]
    return results
