=====================
Excel Template Reader
=====================
.. currentmodule:: pyapacheatlas.readers.excel

.. autosummary::
   :toctree: api/

   ExcelConfiguration
   ExcelReader

The Excel Reader provides an interface to Excel templates and extracting the
content in the standardized Atlas format. That extract can then be uploaded
to your Microsoft Purview or Apache Atlas.

Learn more about the Excel Configuration options here: :doc:`./excel-config`

.. autosummary::
   :toctree: api/

   ExcelReader.parse_bulk_entities
   ExcelReader.parse_entity_defs
   ExcelReader.parse_finegrain_column_lineage
   ExcelReader.parse_table_lineage
   ExcelReader.parse_table_finegrain_column_lineages
   ExcelReader.parse_update_lineage
   ExcelReader.parse_column_mapping
   ExcelReader.parse_update_lineage_with_mappings
   ExcelReader.parse_classification_defs
   ExcelReader.make_template