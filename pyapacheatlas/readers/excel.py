from openpyxl import load_workbook, Workbook

from ..core.entity import AtlasEntity, AtlasProcess
from ..core.util import GuidTracker

class ExcelConfiguration():

    def __init__(self, **kwargs):
        super().__init__()
        # Required attributes:
        # qualifiedName, column, transformation, table
        self.entity_sheet = kwargs.get("column_sheet","columns").lower()
        self.table_sheet = kwargs.get("table_sheet", "tables").lower()
        self.entity_source_prefix = kwargs.get("entity_source_prefix", "source").lower()
        self.entity_target_prefix = kwargs.get("entity_target_prefix", "target").lower()
        self.entity_process_prefix = kwargs.get("entity_process_prefix", "process").lower()
        self.column_transformation_name = kwargs.get("column_transformation_name", "transformation").lower()

def from_excel(filepath, excel_config):

    wb = load_workbook(filepath)

    guid_tracker = GuidTracker(-5000)

    entities = []

    if excel_config.table_sheet in wb.sheetnames:
        ws = wb.get_sheet_by_name(excel_config.table_sheet)
        # Read the first header row
        # Convert the second plus rows to Atlas Entities
        json_sheet = _parse_spreadsheet(ws)
        entities = _parse_table_mapping(json_sheet, excel_config, guid_tracker)

    return entities

def _columns_matching_pattern(row, starts_with, does_not_match = []):
    candidates =  {k:v for k,v in row.items() if str(k).startswith(starts_with)}
    for bad_key in does_not_match:
        if bad_key in candidates:
            candidates.pop(bad_key)
    
    return candidates


def _parse_table_mapping(json_rows, excel_config, guid_tracker):
    # Required attributes
    source_table_column = excel_config.entity_source_prefix+" table"
    source_table_type_column = excel_config.entity_source_prefix+" type"
    target_table_column = excel_config.entity_target_prefix+" table"
    target_table_type_column = excel_config.entity_target_prefix+" type"
    process_name_column = excel_config.entity_process_prefix+" name"
    process_type_column = excel_config.entity_process_prefix+" type"

    # Read in all Source and Target entities
    output = []
    for row in json_rows:
        # Set up defaults
        target_entity, source_entity, process_entity = None, None, None
        # Always expecting a TARGET in the sheet
        target_entity = AtlasEntity(
            name=row[target_table_column],
            typeName=row[target_table_type_column],
            qualified_name=row[target_table_column],
            guid=guid_tracker.get_guid()
            # TODO: Add additional attributes
        )
        output.append(target_entity)
        
        if row[source_table_column] is not None:
            # There is a source table
            source_entity = AtlasEntity(
                name=row[source_table_column],
                typeName=row[source_table_type_column],
                qualified_name=row[source_table_column],
                guid=guid_tracker.get_guid()
                # TODO: Add additional attributes
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
                inputs=[] if source_entity is None else source_entity.to_json(minimum=True),
                outputs=target_entity.to_json(minimum=True)
                # TODO: Add additional attributes
            )
            output.append(process_entity)
        
    # Return all entities
    return output

def _parse_column_mapping(json_columns, excel_config, guid_tracker, atlas_entities, atlas_typedefs):
    """
    :param json_columns:
            A list of dicts that contain the converted rows of your column spreadsheet.
        :type json_columns: list(dict(str,str))
    :param ~pyapacheatlas.readers.excel.ExcelConfiguration excel_config:
            An excel configuation object to indicate any customizations to the template excel.
    :param ~pyapacheatlas.core.util.GuidTracker guid_tracker:
            A guid tracker to be used in incrementing / decrementing the guids in use.
    :param atlas_entities:
            A list of :class:`~pyapacheatlas.core.entity.AtlasEntity` containing the referred entities.
        :type atlas_entities: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
    :param atlas_typedefs:
            A list of :class:`~pyapacheatlas.core.typedef.EntityTypeDef` containing the referred typedefs.
        :type atlas_typedefs: list(:class:`~pyapacheatlas.core.typedef.EntityTypeDef`)
    """
    # Required attributes
    source_table_column = excel_config.entity_source_prefix+" table"
    source_column_name = excel_config.entity_source_prefix+" column"
    target_table_column = excel_config.entity_target_prefix+" table"
    target_column_name = excel_config.entity_target_prefix+" column"
    transformation_column = excel_config.column_transformation_name

    table_to_col_type = {}
    process_to_column_lineage_type = {}

    output = []

    # Read every row
    # There should always be a target column
    # Given the existing table entity in atlas_entities, look up the appropriate column type
    # Add to outputs

    # If there is a source column
    # Given the existing source table entity in atlas_entities, look up the appropriate column type
    # Given the existing process that with target table and source table types, look up the appropriate column_lineage type
    # Add column and process to outputs

    return output


def _parse_spreadsheet(worksheet):
    
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


# def _parse_column_mapping(worksheet, excel_config, process_entities, table_entities = None):
#     # Supporting a column level mapping
#     results = _parse_spreadsheet(worksheet)
#     entity_outputs = []

#     min_guid = -10000
#     if table_entities:
#         min_guid = min([table["guid"] for table in table_entities])

#     active_guid = GuidTracker(starting=min_guid)

#     for row in results:
#         # Should always have the source column
#         # Anything with the prefix should be considered an attribute

#         required_attributes = ["column", "type", "qualifiedname"]

#         process_attributes = ["column lineage process name","column lineage transformation"]

#         source_req_attribs = {i:excel_config.entity_source_prefix+" "+i for i in required_attributes}
        
#         source_entity = AtlasEntity(
#             name = row[source_req_attribs["column"]],
#             typeName = row[source_req_attribs["type"]], # TODO: Incorporate table entity
#             qualified_name = row[source_req_attribs["qualifiedname"]], # TODO: Incorporate table entity
#             guid = active_guid.get_guid(),
#             # The mapping between column and table
#             # TODO: How do I know the relationshipAttributes to apply?
#             relationshipAttributes = {
#               "table": {
#                 "qualifiedName": "qualtargetsc_stock_movement_trx_fct",
#                 "guid": -2000,
#                 "typeName": "azure_sql_table"
#                 }
#             }
#         )
#         source_entity.attributes = _columns_matching_pattern(
#             row, 
#             starts_with=excel_config.entity_source_prefix,
#             does_not_match=source_req_attribs.values()
#         )
#         entity_outputs.append(source_entity)
        
#         # May have a target column
#         if excel_config.entity_target_prefix+" column" in row:

#             target_req_attribs = {i:excel_config.entity_target_prefix+" "+i for i in required_attributes}

#             target_entity = AtlasEntity(
#             name = row[target_req_attribs["column"]],
#             typeName = row[target_req_attribs["type"]], # TODO: Incorporate table entity
#             qualified_name = row[target_req_attribs["qualifiedname"]], # TODO: Incorporate table entity
#             guid = active_guid.get_guid(),
#             # The mapping between column and table
#             # TODO: How do I know the relationshipAttributes to apply?
#             relationshipAttributes = {
#               "table": {
#                 "qualifiedName": "qualtargetcur_stock_movement_trx_fct", # TODO: Extract the correct name
#                 "guid": -2001, # TODO: Extract the correct guid
#                 "typeName": "azure_sql_table" # TODO: Look up the correct mapping
#                 }
#             }
#             )
#             target_entity.attributes = _columns_matching_pattern(
#                 row, 
#                 starts_with=excel_config.entity_target_prefix,
#                 does_not_match=target_req_attribs.values()
#             )

#             # TODO May have a transformation
#             # TODO Anything with the prefix should be considered an attribute
#             entity_outputs.append(target_entity)

#             # TODO: How do I know which process to use?  Consider Process name should be provided?
#             column_lineage_process = AtlasProcess(
#                 name = row["process_name"],
#                 typeName = "demo_sql_column_lineage_process", # TODO: Incorporate table entity
#                 qualified_name = source_entity.qualified_name + "-" + target_entity.qualified_name, # TODO: Incorporate table entity
#                 guid = active_guid.get_guid(),
#                 inputs = [source_entity.to_json(minimum=True)],
#                 outputs= [target_entity.to_json(minimum=True)],
#                 attributes = {"query": table_process.to_json(minimum=True)}
#             )
#             entity_outputs.append(column_lineage_process)
            
#             # If there is a target then there must be a relationship
#             # There may be a transformation
#     return entity_outputs
