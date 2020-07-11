from openpyxl import load_workbook, Workbook

from ..core.entity import AtlasEntity, AtlasProcess
from ..core.util import GuidTracker

class ExcelConfiguration():

    def __init__(self, **kwargs):
        super().__init__()
        # Required attributes:
        # qualifiedName, column, transformation, table
        self.entity_sheet = kwargs.get("entity_sheet","entities")
        self.table_sheet = kwargs.get("table_sheet", "tables")
        self.entity_source_prefix = kwargs.get("entity_source_column", "source").lower()
        self.entity_target_prefix = kwargs.get("entity_target_prefix", "target").lower()

def from_excel(filepath, excel_config):

    wb = load_workbook(filepath)

    entities = []

    if excel_config.entity_sheet in wb.sheetnames:
        ws = wb.get_sheet_by_name(excel_config.entity_sheet)
        entities = _parse_entities_detailed(ws, excel_config)

    return entities

def _columns_matching_pattern(row, starts_with, does_not_match = []):
    candidates =  {k:v for k,v in row.items() if str(k).startswith(starts_with)}
    for bad_key in does_not_match:
        if bad_key in candidates:
            candidates.pop(bad_key)
    
    return candidates


def _parse_spreadsheet(worksheet):
    
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


def _parse_entities_detailed(worksheet, excel_config, process_entities, table_entities = None):
    # Supporting a column level mapping
    results = _parse_spreadsheet(worksheet)
    entity_outputs = []

    min_guid = -10000
    if table_entities:
        min_guid = min([table["guid"] for table in table_entities])

    active_guid = GuidTracker(starting=min_guid)

    for row in results:
        # Should always have the source column
        # Anything with the prefix should be considered an attribute

        required_attributes = ["column", "type", "qualifiedname"]

        process_attributes = ["column lineage process name","column lineage transformation"]

        source_req_attribs = {i:excel_config.entity_source_prefix+" "+i for i in required_attributes}
        
        source_entity = AtlasEntity(
            name = row[source_req_attribs["column"]],
            typeName = row[source_req_attribs["type"]], # TODO: Incorporate table entity
            qualified_name = row[source_req_attribs["qualifiedname"]], # TODO: Incorporate table entity
            guid = active_guid.get_guid(),
            # The mapping between column and table
            # TODO: How do I know the relationshipAttributes to apply?
            relationshipAttributes = {
              "table": {
                "qualifiedName": "qualtargetsc_stock_movement_trx_fct",
                "guid": -2000,
                "typeName": "azure_sql_table"
                }
            }
        )
        source_entity.attributes = _columns_matching_pattern(
            row, 
            starts_with=excel_config.entity_source_prefix,
            does_not_match=source_req_attribs.values()
        )
        entity_outputs.append(source_entity)
        
        # May have a target column
        if excel_config.entity_target_prefix+" column" in row:

            target_req_attribs = {i:excel_config.entity_target_prefix+" "+i for i in required_attributes}

            target_entity = AtlasEntity(
            name = row[target_req_attribs["column"]],
            typeName = row[target_req_attribs["type"]], # TODO: Incorporate table entity
            qualified_name = row[target_req_attribs["qualifiedname"]], # TODO: Incorporate table entity
            guid = active_guid.get_guid(),
            # The mapping between column and table
            # TODO: How do I know the relationshipAttributes to apply?
            relationshipAttributes = {
              "table": {
                "qualifiedName": "qualtargetcur_stock_movement_trx_fct", # TODO: Extract the correct name
                "guid": -2001, # TODO: Extract the correct guid
                "typeName": "azure_sql_table" # TODO: Look up the correct mapping
                }
            }
            )
            target_entity.attributes = _columns_matching_pattern(
                row, 
                starts_with=excel_config.entity_target_prefix,
                does_not_match=target_req_attribs.values()
            )

            # TODO May have a transformation
            # TODO Anything with the prefix should be considered an attribute
            entity_outputs.append(target_entity)

            # TODO: How do I know which process to use?  Consider Process name should be provided?
            column_lineage_process = AtlasProcess(
                name = row["process_name"],
                typeName = "demo_sql_column_lineage_process", # TODO: Incorporate table entity
                qualified_name = source_entity.qualified_name + "-" + target_entity.qualified_name, # TODO: Incorporate table entity
                guid = active_guid.get_guid(),
                inputs = [source_entity.to_json(minimum=True)],
                outputs= [target_entity.to_json(minimum=True)],
                attributes = {"query": table_process.to_json(minimum=True)}
            )
            entity_outputs.append(column_lineage_process)
            
            # If there is a target then there must be a relationship
            # There may be a transformation
    return entity_outputs
