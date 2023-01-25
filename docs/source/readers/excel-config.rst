==========================
Excel Reader Configuration
==========================

This package supports reading a standard template from an excel file.
The following shows how to work with the template file and customization
of the excel file you're reading from. Again, it's assumed that you're
using this excel template to create table and column lineage between a
“target” and “source” set of tables and columns.

Generate Excel Template
=======================

After installing PyApacheAtlas, run this command in the terminal to
create an excel file with the required sheets and columns.

::

   python -m pyapacheatlas --make-template ./template.xlsx

Excel Template Tabs and Their Uses
==================================

The column headers discussed below and that you add are **CASE
SENSITIVE**.

The excel template provides several sheets:

-  BulkEntities - Used to create or update bulk entities.
-  UpdateLineage - Used to create or update lineage (by creating process
   entities that reference your source and target entities).
-  ColumnMapping - Used to update or create a process entity with the
   columnMapping attribute.
-  EntityDefs - Used to quickly define one or many entity types and
   their additional attributes.
-  ClassificationDefs - Used to quickly define one or many
   classifications. This does not support Purview Classification Rules.
-  TablesLineage - (Deprecated) Used to define the Tables involved in
   this batch's column level lineage.
-  FineGrainColumnLineage - (Deprecated) Used to define the Columns
   involved in this batch's column level lineage.

Each tab has a related ``parse_*`` method in the ``ExcelReader``. For
example, to parse the BulkEntities tab, you would call the
``ExcelReader.parse_bulk_entities`` method and pass in the path to the
excel file.

There are two ``parse_`` methods that combine UpdateLineage with
ColumnMapping and TablesLineage with FineGrainColumnLineage.

-  ``parse_update_lineage_with_mappings`` which combines the results of
   UpdateLineage and ColumnMapping
-  ``parse_table_finegrain_column_lineages`` which combines the results
   of TablesLineage and FineGrainColumnLineage.

For bulk entities, update lineage, column mapping, tables lineage, and
columns lineage ``parse_`` methods, you pass the resulting dictionary
directly to the ``client.upload_entities`` method to take the contents
of your spreadsheet and push them to your Atlas / Purview catalog.

BulkEntities tab
----------------

In this tab, you bulk load entities along with their attributes
(e.g. data_type, description, Experts, Owners). The most common use for
this tab is to just upload a set of tables and their respective columns.
One row would represent a table and the multiple rows would represent a
column. In order to make that “relationship” happen, you must provide a
``[Relationship] table`` column and provide the qualified name of the
table entity you defined earlier in the sheet. Without that
[Relationship] table column, the columns would be unattached.

A special note, be sure that your column and table types (as indicated
by the ``typeName`` column) can accept a “Relationship Attribute” of
“table” and “columns” as they are typically defined. See the `Column
Lineage: Hive Bridge
Style <https://github.com/wjohnson/pyapacheatlas/wiki/Column-Lineage:-Hive-Bridge-Style>`__
page for more details on relationships.

Column Headers with Special Meanings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``[Relationship] xyz`` takes the cell's value and adds it to the xyz
   relationship attribute. Replace xyz with whatever your relationship
   attribute's name is (probably “table” if you're relating a column to
   a table).
-  ``[Relationship] meanings`` assigns glossary terms to the entity
   you're uploading. The term you provide (for Purview) must be the
   formal name. If you have a hierarchical term, your formal name will
   look like ``parent term_child term``. You can provide multiple
   meanings / glossary terms by delimiting with a semi-colon (;) by
   default. This is configurable in the ``ExcelConfiguration``.

   -  **Note**: You can only apply classifications to NEW entities by
      the design of the ``/entity/bulk`` endpoint. To update an existing
      entity's classifications, you must do so programmatically with the
      `assignTerm <https://wjohnson.github.io/pyapacheatlas-docs/latest/pyapacheatlas.core.html#pyapacheatlas.core.client.AtlasClient.assignTerm>`__
      method.

-  ``[root] classifications`` assigns classifications to the uploaded
   entity. The value in the spreadsheet must match the classification's
   formal name and not the friendly name. You can provide multiple
   classifications by delimiting with a semi-colon (;) by default. This
   is configurable in the ``ExcelConfiguration``.

   -  **Note**: You can only apply classifications to NEW entities by
      the design of the ``/entity/bulk`` endpoint. To update an existing
      entity's classifications, you must do so programmatically with the
      `classify_bulk_entities <https://wjohnson.github.io/pyapacheatlas-docs/latest/pyapacheatlas.core.html#pyapacheatlas.core.client.AtlasClient.classify_bulk_entities>`__
      or
      `classify_entity <https://wjohnson.github.io/pyapacheatlas-docs/latest/pyapacheatlas.core.html#pyapacheatlas.core.client.AtlasClient.classify_entity>`__
      method.

-  ``experts`` or ``owners`` (for Azure Purview) lets you provide one or
   many Azure Active Directory object ids by delimiting with a
   semi-colon (;) by default. This is configurable in the
   ``ExcelConfiguration``. It only accepts AAD object ids because that
   is what Purview actually stores. The Purview UI calls the Microsoft
   graph API on your behalf. PyApacheAtlas does not do this.
-  ``[root] labels`` (for Apache Atlas this is NOT sensitivity labels
   for Purview) lets you provide one or many labels by delimiting with a
   semi-colon (;) by default. This is configurable in the
   ``ExcelConfiguration``.

   -  **Note**: You can only apply labels to NEW entities by the design
      of the ``/entity/bulk`` endpoint. To update an existing entity's
      labels, you must do so programmatically with the
      ``update_entity_labels`` method.

All remaining column headers will convert into attributes for the given
entity. If the cell is blank for a given column, it will not be added to
the entity.

UpdateLineage tab
-----------------

The Update Lineage tab is meant to create or update lineage between two
or more entities.

In the example below, it creates a Process entity that links the target
and source datasets.

+---------+---------+---------+---------+---------+---------+---------+
| Target  | Target  | Source  | Source  | Process | Process | Process |
| t       | qualif  | t       | qualif  | name    | qualif  | t       |
| ypeName | iedName | ypeName | iedName |         | iedName | ypeName |
+=========+=========+=========+=========+=========+=========+=========+
| DataSet | custom  | DataSet | custom  | My      | custom  | Process |
|         | ://targ |         | ://sour | Custom  | ://proc |         |
|         | et-that |         | ce-that | Process | ess-to- |         |
|         | -exists |         | -exists |         | be-made |         |
+---------+---------+---------+---------+---------+---------+---------+

-  If your target has multiple inputs, you should specify the target
   only once then specify the multiple sources on separate lines with
   the same Process values repeated on each line.
-  If you want to ensure that the Process has an empty list for an input
   or output, put ``N/A`` as the Target or Source qualifiedName (to
   negate the Outputs or Inputs attribute respectively).

ColumnMapping tab
-----------------

The Column Mapping tab takes in a Process entity, the qualified names of
the Source and Target tables, and the column names that should be
mapped. **Note**: Your Process entity type MUST HAVE THE columnMapping
ATTRIBUTE for this to work in Azure Purview. The default Process type
does NOT have this attribute, you must create your own.

+---------+---------+---------+---------+---------+---------+---------+
| Target  | Target  | Source  | Source  | Process | Process | Process |
| column  | qualif  | column  | qualif  | name    | qualif  | t       |
|         | iedName |         | iedName |         | iedName | ypeName |
+=========+=========+=========+=========+=========+=========+=========+
| d       | custom  | colA    | custom  | My      | custom  | Custom  |
| estcolA | ://targ |         | ://sour | Custom  | ://proc | Process |
|         | et-that |         | ce-that | Process | ess-to- |         |
|         | -exists |         | -exists |         | be-made |         |
+---------+---------+---------+---------+---------+---------+---------+
| d       | custom  | colB    | custom  | My      | custom  | Custom  |
| estcolB | ://targ |         | ://sour | Custom  | ://proc | Process |
|         | et-that |         | ce-that | Process | ess-to- |         |
|         | -exists |         | -exists |         | be-made |         |
+---------+---------+---------+---------+---------+---------+---------+
| destc   | custom  | colC    | custom  | My      | custom  | Custom  |
| olCombo | ://targ |         | ://sour | Custom  | ://proc | Process |
|         | et-that |         | ce-that | Process | ess-to- |         |
|         | -exists |         | -exists |         | be-made |         |
+---------+---------+---------+---------+---------+---------+---------+
| destc   | custom  | colD    | custom  | My      | custom  | Custom  |
| olCombo | ://targ |         | ://sour | Custom  | ://proc | Process |
|         | et-that |         | ce-that | Process | ess-to- |         |
|         | -exists |         | -exists |         | be-made |         |
+---------+---------+---------+---------+---------+---------+---------+

This sample will create or update the CustomProcess type with a
qualified name of ``custom://process-to-be-made`` and indicate the
following mappings:

-  From ``custom-source-that-exists`` to ``target-that-exists``\ …

   -  colA maps to destcolA
   -  colB maps to destcolB
   -  colC maps to destcolCombo
   -  colD maps to destcolCombo

This could be altered to have multiple sources and targets with a more
complex mapping.

**Note**: The Source and Target qualified names MUST be inputs and
outputs on the given Process entity for the Purview Lineage UI to show
the column mapping.

EntityDefs tab
--------------

Supports the creation of custom entity types. By default they are
subtypes of DataSet (most common thing you'll need).

Each row represents one attribute that you want to add to your custom
type. The schema section below lists the various fields that can be
filled in. However, if you fill in only the type and attribute name
information, the attribute will be, by default, a string attribute. You
can find additional information about the defaults in the `Apache Atlas
docs <http://atlas.apache.org/api/v2/json_AtlasAttributeDef.html>`__.

.. _column-headers-with-special-meanings-1:

Column Headers with Special Meanings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``Entity superTypes`` this will allow you to define one or many super
   types. If you want to create a custom Process type, you would add
   this column header and enter Process for the relevant row's cell
   value. This is delimited with a semi-colon (;) by default. This is
   configurable in the ``ExcelConfiguration``. This should be specified
   once for the given type all other rows can be left blank for this
   column.

ClassificationDefs tab
----------------------

Supports the creation of classification types. This does not support the
creation of Classification Rules in Azure Purview.

You need only provide the classification name, description, and the
entity types that it should apply to.

The entity types is most likely going to be DataSet by you may be more
specific and specify multiple types in the entityTypes cell by
delimiting with a semi-colon (;) by default. This is configurable in the
``ExcelConfiguration``.

TablesLineage and FineGrainColumnsLineage tabs (DEPRECATED)
-----------------------------------------------------------

These tabs are being deprecated and will not receive new updates.

The Tables and Columns sheets require a set of “Target” and “Source”
excel columns. \* Target / Source table is the unique name of the table.
\* Target / Source column is the column name on that respective table.
Its qualified name will ``{Table}#{Column}``. \* Target / Source type
are the pre-defined table type definitions. \* Process name is the
unique name of the process being used to create the Target from the
Source. \* Process type is the pre-defined type definition. \* Process
name and type are only provided on the Tables sheet. \* Target / Source
classifications are the table or column level classifications. They are
separated by semicolons (;) in the same cell. This can be customized
with the
``ExcelConfiguration(separate * A column Transformation is the expression that generated the column.  For example``\ a
+ b\ ``or``\ CASE WHEN x=1 THEN … ELSE … END`.

In addition, you can provide **additional attributes** for the table or
column by adding another column and using the “Target”, “Source”, or
“Process” prefix.

For example, if you add a “Target data-type” attribute to the Columns
sheet, the ``parse_lineages`` function would add that column's values to
the generated Target entity's attributes. It would appear as:

.. code:: json

   {
   "attributes":{
     "name": "SomeName",
     "qualifiedName": "SomeQualifiedName",
     "data-type": "Value-from-cell"
     }
   }

Required Columns for Each Tab
-----------------------------

This section defines what are the required headers for each tab.

Please note that the column names are **case sensitive** and should
follow Java camelCase style unless otherwise noted.

.. code:: python

   "BulkEntities": [
       "typeName", "name", "qualifiedName"
   ]
   "ClassificationDefs": [
       "classificationName", "entityTypes", "description"
   ]
   "ColumnMapping": [
       "Source qualifiedName", "Source column", "Target qualifiedName", 
       "Target column", "Process qualifiedName", "Process typeName",
       "Process name"
   ]
   "EntityDefs": [
       "Entity TypeName", "name", "description",
       "isOptional", "isUnique", "defaultValue",
       "typeName", "displayName", "valuesMinCount",
       "valuesMaxCount", "cardinality", "includeInNotification",
       "indexType", "isIndexable"
   ]
   "UpdateLineage": [
       "Target typeName", "Target qualifiedName", "Source typeName",
       "Source qualifiedName", "Process name", "Process qualifiedName",
       "Process typeName"
   ]
   "FineGrainColumnLineage": [
       "Target table", "Target column", "Target classifications",
       "Source table", "Source column", "Source classifications",
       "transformation"
   ]
   "TablesLineage": [
       "Target table", "Target type", "Target classifications",
       "Source table", "Source type", "Source classifications",
       "Process name", "Process type"
   ]

Reading Excel using the ``parse_*`` family of methods
=====================================================

The ``parse_*`` functions facilitates reading the excel file and
extracting out the content into Python / Json objects.

There are many
`samples <https://github.com/wjohnson/pyapacheatlas/tree/master/samples/excel>`__
that will populate an example spreadsheet for you.

Customizing the Template and Excel Configuration
================================================

The ``ExcelConfiguration`` class provides the ability to customize how
to read your Excel file.

When you instantiate the ExcelConfiguration, you can provide the
following parameters:

-  column_sheet: The name of the columns sheet. Defaults to “Columns”.
-  table_sheet: The name of the table sheet. Defaults to “Tables”.
-  entityDef_sheet: The name of the entity definition sheet. Defaults to
   “EntityDefs”.
-  source_prefix:Defaults to “Source” and represents the prefix of the
   columns in Excel to be considered related to the source table or
   column.
-  target_prefix: Defaults to “Target” and represents the prefix of the
   columns in Excel to be considered related to the target table or
   column.
-  process_prefix: Defaults to “Process” and represents the prefix of
   the columns in Excel to be considered related to the table process.
-  column_transformation_name: Defaults to “Transformation” and
   identifies the column that represents the transformation for a
   specific column.
-  value_separator: Defaults to ‘;' (semi-colon) and provides the way
   multi-valued fields are parsed (currently only supported for
   classifications).
