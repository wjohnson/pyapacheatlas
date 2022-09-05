=====================
JSON Template Reader
=====================
.. currentmodule:: pyapacheatlas.readers.reader

.. autosummary::
   :toctree: api/

   ReaderConfiguration
   Reader

The Reader provides an interface to JSON / dictionaries and extracting the
content in the standardized Atlas format. That extract can then be uploaded
to your Microsoft Purview or Apache Atlas.

.. autosummary::
   :toctree: api/

   Reader.parse_bulk_entities
   Reader.parse_entity_defs
   Reader.parse_finegrain_column_lineage
   Reader.parse_table_lineage
   Reader.parse_update_lineage
   Reader.parse_column_mapping
   Reader.parse_classification_defs
   Reader.make_template
