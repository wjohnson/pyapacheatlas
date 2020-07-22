import json

from openpyxl import load_workbook, Workbook

from ..core.entity import AtlasEntity, AtlasProcess
from ..core.util import GuidTracker
from .core import to_column_entities
from .core import to_table_entities

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
    entities.extend(to_table_entities(json_sheet, excel_config, guid_tracker))

    # Getting column entities
    column_sheet = wb.get_sheet_by_name(excel_config.column_sheet)
    json_columns = _parse_spreadsheet(column_sheet)
    
    _temp_columns = to_column_entities(json_columns, excel_config, guid_tracker, entities, type_defs, use_column_mapping=use_column_mapping)
    entities.extend(_temp_columns)
    
    output = [e.to_json() for e in entities]

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
    # TODO: Allow for skip lines
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
