============================
Atlas Type Definition Models
============================
.. currentmodule:: pyapacheatlas.core.typedef

.. autosummary::
   :toctree: api/

----------------
Type Definitions
----------------

A type definition enables you to create custom types.

* To create a custom asset type, use the EntityTypeDef
* To create a custom classification, use the ClassificationTypeDef
* To create a custom business metadata definition use StructType and TypeCategory.


.. highlight:: python
.. code-block:: python

   biz_def = AtlasStructDef(
      name="operations",
      category=TypeCategory.BUSINESSMETADATA,
      attributeDefs=[
         AtlasAttributeDef(name="expenseCode",options={"maxStrLength": "500","applicableEntityTypes":"[\"DataSet\"]"}),
         AtlasAttributeDef(name="criticality",options={"maxStrLength": "500", "applicableEntityTypes":"[\"DataSet\"]"})
      ]
   )

* To upload a type definition use the AtlasClient or PurviewClient `upload_typedefs`.


.. highlight:: python
.. code-block:: python

   # Upload an entity definition
   client.upload_typedefs(entityDefs=[entity_def])
   # Upload a business metadata definition
   client.upload_typedefs(businessMetadataDefs=[biz_def])
   # Upload a classification definition
   client.upload_typedefs(classificationDefs=[classif_def])
   # etc.

.. autosummary::
   :toctree: api/

   EntityTypeDef
   ClassificationTypeDef
   RelationshipTypeDef
   Cardinality
   AtlasStructDef
   TypeCategory
   BaseTypeDef
   AtlasAttributeDef
   
------------------------------
Atlas Relationship Definitions
------------------------------

These are utility classes when dealing with defining relationships.

.. autosummary::
   :toctree: api/

   AtlasRelationshipAttributeDef
   AtlasRelationshipEndDef
   ParentEndDef
   ChildEndDef
