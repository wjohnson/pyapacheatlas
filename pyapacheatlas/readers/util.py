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