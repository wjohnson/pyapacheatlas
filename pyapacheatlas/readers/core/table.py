from ...core import AtlasEntity, AtlasProcess
from ..util import *

def to_table_entities(json_rows, excel_config, guid_tracker):
    """
    Converts the "tables" information into Atlas Entities for Target, Source,
    and Process types.  Currently only support one target from one source.

    :param json_rows:
            A list of dicts that contain the converted tables of your column spreadsheet.
        :type json_rows: list(dict(str,str))
    :param ~pyapacheatlas.readers.excel.ExcelConfiguration excel_config:
            An excel configuration object to indicate any customizations to the template excel.
    :param ~pyapacheatlas.core.util.GuidTracker guid_tracker:
            A guid tracker to be used in incrementing / decrementing the guids in use.
    :return: A list of atlas entities that represent your source, target,
        and table processes.
    :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    """
    # Required attributes
    # NOTE: Classification is not actually required but it's being included to avoid being roped in as an attribute
    source_table_name_header = excel_config.entity_source_prefix+" table"
    source_table_type_column = excel_config.entity_source_prefix+" type"
    source_table_classifications_header = excel_config.entity_source_prefix+" classifications"
    required_source_headers = [source_table_name_header, source_table_type_column, source_table_classifications_header]

    target_table_name_header = excel_config.entity_target_prefix+" table"
    target_table_type_column = excel_config.entity_target_prefix+" type"
    target_table_classifications_header = excel_config.entity_target_prefix+" classifications"
    required_target_headers = [target_table_name_header, target_table_type_column, target_table_classifications_header]

    process_name_column = excel_config.entity_process_prefix+" name"
    process_type_column = excel_config.entity_process_prefix+" type"
    required_process_headers = [process_name_column, process_type_column]

    # Read in all Source and Target entities
    output = list() # TODO: Change to a dict to facilitate lookups
    for row in json_rows:
        # Set up defaults
        target_entity, source_entity, process_entity = None, None, None
        # Always expecting a TARGET in the sheet
        target_entity = AtlasEntity(
            name=row[target_table_name_header],
            typeName=row[target_table_type_column],
            # qualifiedName can be overwritten via the attributes functionality
            qualified_name=row[target_table_name_header],
            guid=guid_tracker.get_guid(),
            attributes = columns_matching_pattern(row, excel_config.entity_target_prefix, does_not_match = required_target_headers),
            classifications = string_to_classification(row.get(target_table_classifications_header))
        )
        # TODO: Look up if this is in the output append if not; update attributes and classifications if it is present.
        if target_entity in output:
            # Assumes things like name, type name, are consistent
            poppable_index = output.index(target_entity)
            popped_target = output.pop(poppable_index)
            target_entity.merge(popped_target)

        output.append(target_entity)
        
        if row[source_table_name_header] is not None:
            # There is a source table
            source_entity = AtlasEntity(
                name=row[source_table_name_header],
                typeName=row[source_table_type_column],
                # qualifiedName can be overwritten via the attributes functionality
                qualified_name=row[source_table_name_header],
                guid=guid_tracker.get_guid(),
                attributes = columns_matching_pattern(row, excel_config.entity_source_prefix, does_not_match = required_source_headers),
                classifications = string_to_classification(row.get(source_table_classifications_header))
            )
            if source_entity in output:
                # Assumes things like name, type name, are consistent
                poppable_index = output.index(source_entity)
                popped_source = output.pop(poppable_index)
                source_entity.merge(popped_source)

            output.append(source_entity)

        # Map the source and target tables to a process       
        if row[process_name_column] is not None:
            # There is a process
            process_entity = AtlasProcess(
                name=row[process_name_column],
                typeName=row[process_type_column],
                qualified_name=row[process_name_column],
                guid=guid_tracker.get_guid(),
                inputs=[] if source_entity is None else [source_entity.to_json(minimum=True)],
                outputs=[target_entity.to_json(minimum=True)],
                attributes = columns_matching_pattern(row, excel_config.entity_process_prefix, does_not_match = required_process_headers)
            )
            # TODO: Lookup if it exists already and if it does, update the inputs and outputs and attributes
            if process_entity in output:
                # Assumes things like name, type name, are consistent
                poppable_index = output.index(process_entity)
                popped_process = output.pop(poppable_index)
                process_entity.merge(popped_process)
                
            output.append(process_entity)
        
    # Return all entities
    return output
