============================
AtlasClient for Apache Atlas
============================

.. currentmodule:: pyapacheatlas.core.client

.. autosummary::
   :toctree: api/

   AtlasClient
   

The AtlasClient is meant for Apache Atlas users to interact with Apache Atlas.
It implements nearly all of the
`Apache Atlas API endpoints`_. Some of the APIs
are separated into other clients. For the AtlasClient, there is a
GlossaryClient that provides access to the Glossary API endpoints.

.. _Apache Atlas API endpoints: https://atlas.apache.org/api/v2/

.. autosummary::
   :toctree: api/
   :caption: Entities

   AtlasClient.get_entity
   AtlasClient.get_single_entity
   AtlasClient.get_entity_header
   AtlasClient.upload_entities
   AtlasClient.partial_update_entity
   AtlasClient.delete_entity
   
   AtlasClient.get_relationship
   AtlasClient.upload_relationship
   AtlasClient.delete_relationship

   AtlasClient.get_all_typedefs
   AtlasClient.get_typedef
   AtlasClient.upload_typedefs
   AtlasClient.delete_type
   AtlasClient.delete_typedefs
   AtlasClient._get_typedefs_header

   AtlasClient.get_entity_classification
   AtlasClient.get_entity_classifications
   AtlasClient.classify_bulk_entities
   AtlasClient.classify_entity
   AtlasClient._classify_entity_adds
   AtlasClient._classify_entity_updates
   AtlasClient.declassify_entity
   
   AtlasClient.update_businessMetadata
   AtlasClient.delete_businessMetadata

   AtlasClient.get_entity_lineage

   AtlasClient.get_glossary
   AtlasClient.get_glossary_term
   AtlasClient.upload_terms
   AtlasClient.get_termAssignedEntities
   AtlasClient.assignTerm
   AtlasClient.delete_assignedTerm

   AtlasClient.update_entity_labels
   AtlasClient.delete_entity_labels