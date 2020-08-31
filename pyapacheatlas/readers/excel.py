import json

from openpyxl import load_workbook, Workbook

from ..core.entity import AtlasEntity, AtlasProcess
from ..core.util import GuidTracker
from .core import to_column_entities
from .core import to_table_entities
from .core import to_entityDefs

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

    def __init__(self, column_sheet="Columns", table_sheet="Tables", 
        entityDef_sheet = "EntityDefs", **kwargs):
        """
        The following parameters apply to the 
        :param str column_sheet: Defaults to "Columns"
        :param str table_sheet: Defaults to "Tables"
        :param str entityDef_sheet: Defaults to "EntityDefs"
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
        self.column_sheet = column_sheet
        self.table_sheet = table_sheet
        self.entityDef_sheet = entityDef_sheet
        self.entity_source_prefix = kwargs.get("entity_source_prefix", "source").lower()
        self.entity_target_prefix = kwargs.get("entity_target_prefix", "target").lower()
        self.entity_process_prefix = kwargs.get("entity_process_prefix", "process").lower()
        self.column_transformation_name = kwargs.get("column_transformation_name", "transformation").lower()


def from_excel(filepath, excel_config, atlas_typedefs, use_column_mapping = False):
    """
    Wrapper for excel_columnLineage function.  To be later used as a wrapper
    for the entire excel_* family.

    :param str filepath: The xlsx file that contains your table and columns.
    :param excel_config: 
        An excel configuration object that is customized to
        your intended spreadsheet.
        :type: :class:`~pyapacheatlas.readers.excel.ExcelConfiguration`
    :param dict(str,list(dict)) atlas_typedefs:
        The results of requesting all type defs from Apache Atlas, including
        entityDefs, relationshipDefs, etc.  relationshipDefs are the only
        values used.
    :param bool use_column_mapping:
        Should the table processes include the columnMappings attribute
        that represents Column Lineage in Azure Data Catalog.
        Defaults to False.
    :return: A list of Atlas Entities representing the spreadsheet's inputs as their json dicts.
    :rtype: list(dict)
    """

    output = excel_columnLineage(filepath, excel_config, atlas_typedefs, use_column_mapping)

    return output


def excel_columnLineage(filepath, excel_config, atlas_typedefs, use_column_mapping = False):
    """
    Read a given excel file that conforms to the excel atlas template and 
    parse the tables, processes, and columns into table and column lineages.
    Requires that the relationship attributes are already defined in the
    provided atlas type defs.

    Infers column type from the target table type and an assumed "columns"
    relationship attribute on the table type.

    Infers the column lineage process based on the provided table process
    (provided in the template's table excel sheet).  Looks for the first
    relationship type def with an endDef2 of `columnLineages`.

    :param str filepath: The xlsx file that contains your table and columns.
    :param excel_config: 
        An excel configuration object that is customized to
        your intended spreadsheet.
        :type: :class:`~pyapacheatlas.readers.excel.ExcelConfiguration`
    :param dict(str,list(dict)) atlas_typedefs:
        The results of requesting all type defs from Apache Atlas, including
        entityDefs, relationshipDefs, etc.  relationshipDefs are the only
        values used.
    :param bool use_column_mapping:
        Should the table processes include the columnMappings attribute
        that represents Column Lineage in Azure Data Catalog.
        Defaults to False.
    :return: A list of Atlas Entities representing the spreadsheet's inputs as their json dicts.
    :rtype: list(dict)
    """

    wb = load_workbook(filepath)

    guid_tracker = GuidTracker(-5000)

    entities = []

    if excel_config.table_sheet not in wb.sheetnames:
        raise KeyError("The sheet {} was not found".format(excel_config.table_sheet))
    if excel_config.column_sheet not in wb.sheetnames:
        raise KeyError("The sheet {} was not found".format(excel_config.column_sheet))
    
    # Getting table entities
    table_sheet = wb[excel_config.table_sheet]
    json_sheet = _parse_spreadsheet(table_sheet)
    entities.extend(to_table_entities(json_sheet, excel_config, guid_tracker))

    # Getting column entities
    column_sheet = wb[excel_config.column_sheet]
    json_columns = _parse_spreadsheet(column_sheet)
    
    _temp_columns = to_column_entities(json_columns, excel_config, guid_tracker, entities, atlas_typedefs, use_column_mapping=use_column_mapping)
    entities.extend(_temp_columns)
    
    output = [e.to_json() for e in entities]

    return output


def excel_typeDefs(filepath, excel_config):
    """
    Read a given excel file that conforms to the excel atlas template and 
    parse the type def tab(s) into a set of entity defs that can be uploaded.

    Currently, only entityDefs are supported.

    :param str filepath: The xlsx file that contains your table and columns.
    :param excel_config: 
        An excel configuration object that is customized to
        your intended spreadsheet.
        :type: :class:`~pyapacheatlas.readers.excel.ExcelConfiguration`
    :return: An AtlasTypeDef with entityDefs for the provided rows.
    :rtype: dict(str, list(dict))
    """
    wb = load_workbook(filepath)
    # A user may omit the entityDef_sheet by providing the config with None
    if excel_config.entityDef_sheet and excel_config.entityDef_sheet not in wb.sheetnames:
        raise KeyError("The sheet {} was not found".format(excel_config.entityDef_sheet))
    
    output = dict()

    # Getting entityDefinitions if the user provided a name of the sheet
    if excel_config.entityDef_sheet:
        entityDef_sheet = wb[excel_config.entityDef_sheet]
        json_entitydefs = _parse_spreadsheet(entityDef_sheet, lowercase_headers = False)
        entityDefs_generated = to_entityDefs(json_entitydefs)
        output.update(entityDefs_generated)
    
    # TODO: Add in classificationDefs and relationshipDefs
    return output


def _parse_spreadsheet(worksheet, lowercase_headers = True):
    """
    Standardizes the excel worksheet into a json format and lowercases
    the column headers.

    :param openpyxl.workbook.Workbook worksheet:
        A worksheet class from openpyxl.
    :param boolean lowercase_headers: 
        Whether headers in the excel spreadsheet should be lowercased.  This
        is important for typeDefs pulling the exact attribute metadata from
        the header.
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

    header_casing = lambda s: s
    if lowercase_headers:
        header_casing = lambda s: s.lower()

    output = []
    for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, min_col=1, max_col=worksheet.max_column):
        output.append({header_casing(k):row[idx].value for idx, k in column_headers})
    
    return output
