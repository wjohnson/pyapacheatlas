import json

from openpyxl import load_workbook, Workbook

from ..core.entity import AtlasEntity, AtlasProcess
from ..core.util import GuidTracker
from .util import (
    child_type_from_relationship, 
    first_entity_matching_attribute, 
    first_process_matching_io,
    from_process_lookup_col_lineage,
    string_to_classification
)

class ExcelConfiguration():
    """
    A configuration utility to understand how your Excel file is structured.

    You must have a "Columns" and "Tables" sheet.  The name is configurable
    with the column_sheet and table_sheet properties.

    The Columns sheet must contain a "Source/Target" Column and Table header.
    Optionally, a Classifications column can be provided for each Source/Target.

    The Tables sheet must contain a "Source/Target" Table and Type along with a 
    Process Name and Process Type.  The Process is related to the mechanism by
    which source becomes the target (e.g. a Stored Procedure or Query).
    """

    def __init__(self, **kwargs):
        """
        The following parameters apply to the 
        :param str column_sheet: Defaults to "Columns"
        :param str table_sheet: Defaults to "Tables"
        :param str entity_source_prefix:
            Defaults to "source" and represents the prefix of the columns
            in Excel to be considered related to the source table or column.
        :param str entity_target_prefix: 
            Defaults to "target" and represents the prefix of the columns
            in Excel to be considered related to the target table or column.
        :param str entity_process_prefix: 
            Defaults to "process" and represents the prefix of the columns
            in Excel to be considered related to the table process.
        :param str column_transformation_name: 
            Defaults to "transformation" and identifies the column that
            represents the transformation for a specific column.        
        """

        super().__init__()
        # Required attributes:
        # qualifiedName, column, transformation, table
        self.column_sheet = kwargs.get("column_sheet","Columns")
        self.table_sheet = kwargs.get("table_sheet", "Tables")
        self.entity_source_prefix = kwargs.get("entity_source_prefix", "source").lower()
        self.entity_target_prefix = kwargs.get("entity_target_prefix", "target").lower()
        self.entity_process_prefix = kwargs.get("entity_process_prefix", "process").lower()
        self.column_transformation_name = kwargs.get("column_transformation_name", "transformation").lower()

def from_excel(filepath, excel_config, type_defs, use_column_mapping = False):
    """
    The core function that wraps the rest of the excel reader.

    :param str filepath: The xlsx file that contains your table and columns.
    :param excel_config: 
        An excel configuration object that is customized to
        your intended spreadsheet.
        :type: :class:`~pyapacheatlas.readers.excel.ExcelConfiguration`
    :param type_defs:
        A list of Atlas type definitions as dictionaries.
        :type: list(dict)
    :param bool use_column_mapping:
        Should the table processes include the columnMappings attribute
        that represents Column Lineage in Azure Data Catalog.
        Defaults to False.
    :return: A list of Atlas Entities representing the spreadsheet's inputs.
    :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    """

    wb = load_workbook(filepath)

    guid_tracker = GuidTracker(-5000)

    entities = []

    if excel_config.table_sheet not in wb.sheetnames:
        raise KeyError("The sheet {} was not found".format(excel_config.table_sheet))
    if excel_config.column_sheet not in wb.sheetnames:
        raise KeyError("The sheet {} was not found".format(excel_config.column_sheet))
    
    # Getting table entities
    table_sheet = wb.get_sheet_by_name(excel_config.table_sheet)
    json_sheet = _parse_spreadsheet(table_sheet)
    entities.extend(_parse_table_mapping(json_sheet, excel_config, guid_tracker))

    # Getting column entities
    column_sheet = wb.get_sheet_by_name(excel_config.column_sheet)
    json_columns = _parse_spreadsheet(column_sheet)
    
    _temp_columns = _parse_column_mapping(json_columns, excel_config, guid_tracker, entities, type_defs, use_column_mapping=use_column_mapping)
    entities.extend(_temp_columns)
    
    output = [e.to_json() for e in entities]

    return output

def _columns_matching_pattern(row, starts_with, does_not_match = []):
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
    candidates =  {k:v for k,v in row.items() if str(k).startswith(starts_with)}
    for bad_key in does_not_match:
        if bad_key in candidates:
            candidates.pop(bad_key)
    candidates = {k[len(starts_with):].strip():v for k,v in candidates.items()}
    
    return candidates


def _parse_table_mapping(json_rows, excel_config, guid_tracker):
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
    source_table_classifications_header = excel_config.entity_target_prefix+" classifications"
    required_source_headers = [source_table_name_header, source_table_type_column, source_table_classifications_header]

    target_table_name_header = excel_config.entity_target_prefix+" table"
    target_table_type_column = excel_config.entity_target_prefix+" type"
    target_table_classifications_header = excel_config.entity_target_prefix+" classifications"
    required_target_headers = [target_table_name_header, target_table_type_column, target_table_classifications_header]

    process_name_column = excel_config.entity_process_prefix+" name"
    process_type_column = excel_config.entity_process_prefix+" type"
    required_process_headers = [process_name_column, process_type_column]

    # Read in all Source and Target entities
    output = []
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
            attributes = _columns_matching_pattern(row, excel_config.entity_target_prefix, does_not_match = required_target_headers),
            classifications = string_to_classification(row.get(target_table_classifications_header))
        )
        output.append(target_entity)
        
        if row[source_table_name_header] is not None:
            # There is a source table
            source_entity = AtlasEntity(
                name=row[source_table_name_header],
                typeName=row[source_table_type_column],
                # qualifiedName can be overwritten via the attributes functionality
                qualified_name=row[source_table_name_header],
                guid=guid_tracker.get_guid(),
                attributes = _columns_matching_pattern(row, excel_config.entity_source_prefix, does_not_match = required_source_headers),
                classifications = string_to_classification(row.get(source_table_classifications_header))
            )
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
                attributes = _columns_matching_pattern(row, excel_config.entity_process_prefix, does_not_match = required_process_headers)
            )
            output.append(process_entity)
        
    # Return all entities
    return output


def _parse_column_mapping(json_rows, excel_config, guid_tracker, atlas_entities, atlas_typedefs, use_column_mapping=False):
    """
    :param json_rows:
            A list of dicts that contain the converted rows of your column spreadsheet.
        :type json_rows: list(dict(str,str))
    :param ~pyapacheatlas.readers.excel.ExcelConfiguration excel_config:
            An excel configuration object to indicate any customizations to the template excel.
    :param ~pyapacheatlas.core.util.GuidTracker guid_tracker:
            A guid tracker to be used in incrementing / decrementing the guids in use.
    :param atlas_entities:
            A list of :class:`~pyapacheatlas.core.entity.AtlasEntity` containing the referred entities.
        :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :param atlas_typedefs:
            A list of :class:`~pyapacheatlas.core.typedef.EntityTypeDef` containing the referred typedefs.
        :type atlas_typedefs: list(:class:`~pyapacheatlas.core.typedef.EntityTypeDef`)
    :param bool use_column_mapping:
            Should the table processes include the columnMappings attribute
            that represents Column Lineage in Azure Data Catalog.
            Defaults to False.
    :return: A list of atlas entities that represent your column source, target,
        and column lineage processes.
    :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    """
    # Required attributes
    # NOTE: Classification is not actually required but it's being included to avoid being roped in as an attribute
    source_table_name_header = excel_config.entity_source_prefix+" table"
    source_column_name_header = excel_config.entity_source_prefix+" column"
    source_column_classifications_header = excel_config.entity_source_prefix+" classifications"
    required_source_headers = [source_column_name_header, source_table_name_header, source_column_classifications_header]
    
    target_table_name_header = excel_config.entity_target_prefix+" table"
    target_column_name_header = excel_config.entity_target_prefix+" column"
    target_column_classifications_header = excel_config.entity_target_prefix+" classifications"
    required_target_headers = [target_column_name_header, target_table_name_header, target_column_classifications_header]
    
    transformation_column_header = excel_config.column_transformation_name
    # No required process headers

    output = []
    tables = {}
    dataset_mapping = {} # table_process_guid: {"input_table":"","output_table":"","columnMapping":[]}
    table_and_proc_mappings ={}

    for row in json_rows:
        # Set up defaults
        target_entity, source_entity, process_entity = None, None, None
        target_entity_table_name, source_entity_table_name = None, None
        # Given the existing table entity in atlas_entities, look up the appropriate column type
        target_entity_table_name = row[target_table_name_header]
        if target_entity_table_name not in tables:
            target_table_entity = first_entity_matching_attribute("name", target_entity_table_name, atlas_entities)
            tables[target_entity_table_name] = target_table_entity
        
        target_col_type = child_type_from_relationship("columns", atlas_typedefs, normalize=True)

        
        # There should always be a target
        target_entity = AtlasEntity(
            name=row[target_column_name_header],
            typeName=target_col_type,
            # qualifiedName can be overwritten via the attributes functionality
            qualified_name=target_entity_table_name+"."+row[target_column_name_header],
            guid=guid_tracker.get_guid(),
            attributes = _columns_matching_pattern(row, excel_config.entity_target_prefix, does_not_match = required_target_headers),
            # TODO: Make the relationship name more dynamic instead of hard coding table
            relationshipAttributes = {"table":tables[target_entity_table_name].to_json(minimum=True)},
            classifications = string_to_classification(row.get(target_column_classifications_header))
        )
        # Add to outputs
        output.append(target_entity)
    
        # Source Column is optiona in the spreadsheet
        if row[source_table_name_header] is not None:
            # Given the existing source table entity in atlas_entities, look up the appropriate column type
            source_entity_table_name = row[source_table_name_header]
            
            if source_entity_table_name not in tables:
                source_table_entity = first_entity_matching_attribute("name", source_entity_table_name, atlas_entities)
                tables[source_entity_table_name] = source_table_entity
            
            source_col_type = child_type_from_relationship("columns", atlas_typedefs, normalize=True)

            source_entity = AtlasEntity(
                name=row[source_column_name_header],
                typeName=source_col_type,
                # qualifiedName can be overwritten via the attributes functionality
                qualified_name=source_entity_table_name+"."+row[source_column_name_header],
                guid=guid_tracker.get_guid(),
                attributes = _columns_matching_pattern(row, excel_config.entity_source_prefix, does_not_match = required_source_headers),
                # TODO: Make the relationship name more dynamic instead of hard coding query
                relationshipAttributes = {"table":tables[source_entity_table_name].to_json(minimum=True)},
                classifications = string_to_classification(row.get(source_column_classifications_header))
            )
            # Add to outputs
            output.append(source_entity)
    
        # Given the existing process that with target table and source table types, 
        # look up the appropriate column_lineage type
        table_process = first_process_matching_io(source_entity_table_name, target_entity_table_name, atlas_entities)

        table_and_proc_mappings, process_type =(
            from_process_lookup_col_lineage(
                table_process.get_name(), 
                table_and_proc_mappings, 
                atlas_entities, 
                atlas_typedefs
            )
        )
        # Assuming there is always a Process for adding at least the target table
        process_attributes = _columns_matching_pattern(row, excel_config.entity_process_prefix)
        process_attributes.update({"dependencyType":"SIMPLE"})
        if row[transformation_column_header] is not None:
            process_attributes.update({"dependencyType":"EXPRESSION", "expression":row[transformation_column_header]})

        process_entity = AtlasProcess(
            name=table_process.get_name(),
            typeName=process_type,
            # qualifiedName can be overwritten via the attributes functionality
            qualified_name=table_process.get_name() + "derived_column:{}_{}".format(
                "NA" if source_entity is None else source_entity.get_name(),
                target_entity.get_name()
            ),
            guid=guid_tracker.get_guid(),
            # Assuming always a single output
            inputs=[] if source_entity is None else [source_entity.to_json(minimum=True)],
            outputs=[target_entity.to_json(minimum=True)],
            attributes = process_attributes,
            # TODO: Make the relationship name more dynamic instead of hard coding query
            relationshipAttributes = {"query":table_process.to_json(minimum=True)}
        )
        output.append(process_entity)

        if use_column_mapping:
            # This is assuming only one dataset in the table process
            col_map_source_col = "*" if source_entity is None else source_entity.get_name()
            col_map_target_col = target_entity.get_name()
            col_map_source_table = next(iter(table_process.attributes["inputs"]), {}).get("qualifiedName") or "*"
            col_map_target_table = table_process.attributes["outputs"][0]["qualifiedName"]
            hash_key = hash(col_map_source_col + col_map_source_table)
            col_map_dict = {"Source":col_map_source_col ,"Sink":col_map_target_col}
            data_map_dict = {"Source":col_map_source_table,"Sink":col_map_target_table}

            if table_process.guid in dataset_mapping:
                if hash_key in dataset_mapping[table_process.guid]:
                    dataset_mapping[table_process.guid][hash_key]["ColumnMapping"].append(col_map_dict)
                else:
                    dataset_mapping[table_process.guid][hash_key]={
                        "ColumnMapping":[col_map_dict],
                        "DatasetMapping": data_map_dict
                    }
            else:
                dataset_mapping[table_process.guid]={
                    hash_key:{
                        "ColumnMapping":[col_map_dict],
                        "DatasetMapping": data_map_dict
                    }
                }
    # Update the passed in atlas_entities if we are using column mapping
    if use_column_mapping:
        for entity in atlas_entities:
            if entity.guid in dataset_mapping:
                column_mapping_attribute = [mappings for mappings in dataset_mapping[entity.guid].values()]
                entity.attributes.update(
                    {"columnMapping":json.dumps(column_mapping_attribute)}
                )

    return output


def _parse_spreadsheet(worksheet):
    """
    Standardizes the excel worksheet into a json format and lowercases
    the column headers.

    :param openpyxl.workbook.Workbook worksheet:
        A worksheet class from openpyxl.
    :return: The standardized version of the excel spreadsheet in json form.
    :rtype: list(dict(str,str))
    """
    
    # Standardize the column header
    column_headers = list(
        zip(
            range(0, len(worksheet[1])), 
            [str(c.value).strip() for c in worksheet[1]]
        )
    )

    output = []
    for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
        output.append({k.lower():row[idx].value for idx, k in column_headers})
    
    return output
