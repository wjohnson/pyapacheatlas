from openpyxl import Workbook
from string import ascii_uppercase

COLUMN_TEMPLATE = [
    "Target Table", "Target Column", "Target Classifications",
    "Source Table", "Source Column", "Source Classifications",
    "Transformation"
]
TABLE_TEMPLATE = [
    "Target Table", "Target Type", "Target Classifications",
    "Source Table", "Source Type", "Source Classifications",
    "Process Name", "Process Type"
]


def make_template(filepath):
    """
    Generate an Excel template file and write it out to the given filepath.

    :param str filepath: The file path to store an XLSX file with the 
        template Tables and Columns sheets.
    """
    wb = Workbook()
    columns = wb.active
    columns.title = "Columns"
    tables = wb.create_sheet("Tables")

    for idx, val in enumerate(COLUMN_TEMPLATE):
        # TODO: Not the best way once we get past 26 columns in the template
        active_column = ascii_uppercase[idx]
        active_value = COLUMN_TEMPLATE[idx]
        active_cell = "{}1".format(active_column)
        columns[active_cell] = active_value
        columns.column_dimensions[active_column].width = len(active_value)

    for idx, val in enumerate(TABLE_TEMPLATE):
        # TODO: Not the best way once we get past 26 columns in the template
        active_column = ascii_uppercase[idx]
        active_value = TABLE_TEMPLATE[idx]
        active_cell = "{}1".format(active_column)
        tables[active_cell] = active_value
        tables.column_dimensions[active_column].width = len(active_value)

    wb.save(filepath)
    wb.close()
