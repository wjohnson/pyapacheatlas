===================================
PurviewClient for Microsoft Purview
===================================
.. currentmodule:: pyapacheatlas.core.client

.. autosummary::
   :toctree: api/

   PurviewClient

The PurviewClient is meant for Microsoft Purview users to interact with the
Apache Atlas APIs and a limited set of Microsoft Purview specific APIs.
It implements nearly all of the below endpoints and the table of methods
below are presented in this order.

* Entity_
* Types_
* Lineage_
* Relationship_

.. _Entity: https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/entity
.. _Types: https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/types
.. _Lineage: https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/lineage
.. _Relationship: https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/relationship

Some of the APIs are separated into other clients. For the PurviewClient, there
is a PurviewGlossaryClient that provides access to the Glossary API endpoints,
a PurviewDiscoveryClient that provides access to the Discovery API endpoints,
and a CollectionsClient that provides access to the Microsoft Purview only
collections APIs.

* Glossary
* Discovery(Search)
* Collections

.. autosummary::
   :toctree: api/

   PurviewClient.get_entity
   PurviewClient.get_single_entity
   PurviewClient.get_entity_header
   PurviewClient.upload_entities
   PurviewClient.partial_update_entity
   PurviewClient.delete_entity
   
   PurviewClient.get_all_typedefs
   PurviewClient.get_typedef
   PurviewClient.upload_typedefs
   PurviewClient.delete_type
   PurviewClient.delete_typedefs
   PurviewClient._get_typedefs_header

   PurviewClient.get_entity_classification
   PurviewClient.get_entity_classifications
   PurviewClient.classify_bulk_entities
   PurviewClient.classify_entity
   PurviewClient._classify_entity_adds
   PurviewClient._classify_entity_updates
   PurviewClient.declassify_entity

   PurviewClient.update_businessMetadata
   PurviewClient.delete_businessMetadata

   PurviewClient.get_entity_lineage
   PurviewClient.get_entity_next_lineage

   PurviewClient.get_relationship
   PurviewClient.upload_relationship
   PurviewClient.delete_relationship

   PurviewClient.update_entity_labels
   PurviewClient.delete_entity_labels