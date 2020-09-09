from string import ascii_uppercase

from openpyxl import Workbook
from openpyxl import load_workbook

from .reader import Reader, ReaderConfiguration


class ExcelConfiguration(ReaderConfiguration):
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

    def __init__(self, column_sheet="ColumnsLineage",
                 table_sheet="TablesLineage",
                 entityDef_sheet="EntityDefs", bulkEntity_sheet="BulkEntities",
                 **kwargs):
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

        super().__init__(**kwargs)
        # Required attributes:
        # qualifiedName, column, transformation, table
        self.column_sheet = column_sheet
        self.table_sheet = table_sheet
        self.entityDef_sheet = entityDef_sheet
        self.bulkEntity_sheet = bulkEntity_sheet


class ExcelReader(Reader):
    @staticmethod
    def _parse_spreadsheet(worksheet):
        """
        Standardizes the excel worksheet into a json format.

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
        for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row, 
            min_col=1, max_col=worksheet.max_column):
            output.append(
                {k: row[idx].value for idx, k in column_headers})

        return output

    def parse_bulk_entities(self, filepath):
        """
        Generate a set of entities from an excel template file.

        :param str filepath: The xlsx file that contains your table and columns.
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        wb = load_workbook(filepath)
        # A user may omit the entityDef_sheet by providing the config with None
        if self.config.bulkEntity_sheet and self.config.bulkEntity_sheet not in wb.sheetnames:
            raise KeyError("The sheet {} was not found".format(
                self.config.entityDef_sheet))

        output = dict()

        if self.config.bulkEntity_sheet:
            bulkEntity_sheet = wb[self.config.bulkEntity_sheet]
            json_bulkEntities = ExcelReader._parse_spreadsheet(
                bulkEntity_sheet)
            bulkEntities_generated = super().parse_bulk_entities(json_bulkEntities)
            output.update(bulkEntities_generated)

        wb.close()

        return output

    def parse_entity_defs(self, filepath):
        """
        Read a given excel file that conforms to the excel atlas template and
        parse the type def tab(s) into a set of entity defs that can be uploaded.

        Currently, only entityDefs are supported.

        :param str filepath: The xlsx file that contains your table and columns.
        :return: An AtlasTypeDef with entityDefs for the provided rows.
        :rtype: dict(str, list(dict))
        """
        wb = load_workbook(filepath)
        # A user may omit the entityDef_sheet by providing the config with None
        if self.config.entityDef_sheet and self.config.entityDef_sheet not in wb.sheetnames:
            raise KeyError("The sheet {} was not found".format(
                self.config.entityDef_sheet))

        output = dict()

        # Getting entityDefinitions if the user provided a name of the sheet
        if self.config.entityDef_sheet:
            entityDef_sheet = wb[self.config.entityDef_sheet]
            json_entitydefs = ExcelReader._parse_spreadsheet(entityDef_sheet)
            entityDefs_generated = super().parse_entity_defs(json_entitydefs)
            output.update(entityDefs_generated)

        wb.close()
        # TODO: Add in classificationDefs and relationshipDefs
        return output

    def parse_column_lineage(self, filepath, atlas_entities, atlas_typedefs, use_column_mapping=False):
        """
        Read a given excel file that conforms to the excel atlas template and
        parse the columns into column lineages.
        Requires that the relationship attributes are already defined in the
        provided atlas type defs.

        Infers column type from the target table type and an assumed "columns"
        relationship attribute on the table type.

        Infers the column lineage process based on the provided table process
        (provided in the template's table excel sheet).  Looks for the first
        relationship type def with an endDef2 of `columnLineages`.

        :param str filepath: The xlsx file that contains your table and columns.
        :param list() atlas_entities:
            A list of AtlasEntity objects representing 
        :param dict(str,list(dict)) atlas_typedefs:
            The results of requesting all type defs from Apache Atlas, including
            entityDefs, relationshipDefs, etc.  relationshipDefs are the only
            values used.
        :param bool use_column_mapping:
            Should the table processes include the columnMappings attribute
            that represents Column Lineage in Azure Data Catalog.
            Defaults to False.
        :return: A list of Atlas Entities representing the spreadsheet's inputs as their json dicts.
        :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
        """

        wb = load_workbook(filepath)

        if self.config.column_sheet not in wb.sheetnames:
            raise KeyError("The sheet {} was not found".format(
                self.config.column_sheet))

        # Getting column entities
        column_sheet = wb[self.config.column_sheet]
        json_columns = ExcelReader._parse_spreadsheet(column_sheet)

        entities = super().parse_column_lineage(
            json_columns,
            atlas_entities,
            atlas_typedefs,
            use_column_mapping=use_column_mapping
        )

        wb.close()

        return entities

    def parse_table_lineage(self, filepath):
        """
        Read a given excel file that conforms to the excel atlas template and
        parse the tables and processes table lineages.
        Requires that the relationship attributes are already defined in the
        provided atlas type defs.

        :param str filepath: The xlsx file that contains your table and columns.

        :return: A list of Atlas Entities representing the spreadsheet's inputs as their json dicts.
        :rtype: list(:class:`~pyapacheatlas.core.entity.AtlasEntity`)
        """

        wb = load_workbook(filepath)

        entities = []

        if self.config.table_sheet not in wb.sheetnames:
            raise KeyError("The sheet {} was not found".format(
                self.config.table_sheet))

        # Getting table entities
        table_sheet = wb[self.config.table_sheet]
        json_sheet = ExcelReader._parse_spreadsheet(table_sheet)
        entities = super().parse_table_lineage(json_sheet)

        wb.close()

        return entities

    def parse_lineages(self, filepath, atlas_typedefs, use_column_mapping=False):
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
        entities = []

        table_entities = self.parse_table_lineage(filepath)
        entities.extend(table_entities)

        # Modifies table_entities if use_column_mapping is True
        column_entities = self.parse_column_lineage(
            filepath,
            table_entities,
            atlas_typedefs,
            use_column_mapping
        )
        entities.extend(column_entities)

        output = [e.to_json() for e in entities]

        return output

    @staticmethod
    def _update_sheet_headers(headers, worksheet):
        """
        For the given worksheet, make the first row equal to the list passed
        in as the headers.

        :param list headers: A list of column headers to use for this sheet.
        :param worksheet:
            The worksheet you are updating.
        :type worksheet:
            :class:`~openpyxl.worksheet.worksheet.Worksheet`
        """
        for idx, val in enumerate(headers):
            # TODO: Not the best way once we get past 26 columns in the template
            active_column = ascii_uppercase[idx]
            active_value = headers[idx]
            active_cell = "{}1".format(active_column)
            worksheet[active_cell] = active_value
            worksheet.column_dimensions[active_column].width = len(
                active_value)

    @staticmethod
    def make_template(filepath):
        """
        Generate an Excel template file and write it out to the given filepath.

        :param str filepath: The file path to store an XLSX file with the
            template Tables and Columns sheets.
        """
        wb = Workbook()
        columnsSheet = wb.active
        columnsSheet.title = "ColumnsLineage"
        tablesSheet = wb.create_sheet("TablesLineage")
        entityDefsSheet = wb.create_sheet("EntityDefs")
        bulkEntitiesSheet = wb.create_sheet("BulkEntities")

        ExcelReader._update_sheet_headers(
            Reader.TEMPLATE_HEADERS["ColumnsLineage"], columnsSheet
        )
        ExcelReader._update_sheet_headers(
            Reader.TEMPLATE_HEADERS["TablesLineage"], tablesSheet
        )
        ExcelReader._update_sheet_headers(
            Reader.TEMPLATE_HEADERS["EntityDefs"], entityDefsSheet
        )
        ExcelReader._update_sheet_headers(
            Reader.TEMPLATE_HEADERS["BulkEntities"], bulkEntitiesSheet
        )

        wb.save(filepath)
        wb.close()
