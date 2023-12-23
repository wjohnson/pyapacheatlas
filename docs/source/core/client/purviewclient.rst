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

Some of the APIs (in the documentation) are separated into other clients. You
do not need to instatiate these clients. They are made available in the PurviewClient.
For the PurviewClient, there is a PurviewGlossaryClient that provides access to the
Glossary API endpoints, a PurviewDiscoveryClient that provides access to the Discovery
API endpoints, a CollectionsClient that provides access to the Microsoft Purview only
collections APIs, an MSGraphClient that provides access to Microsoft Graph Utilities
for converting email addresses to object ids, and a GraphQL client for querying
Microsoft Purview via the preview GraphQL endpoint.

* :ref:`Glossary <glossary-client>`
* :ref:`Discovery(Search) <discovery-client>`
* :ref:`Collections <collections-client>`
* :ref:`Microsoft Graph (for email to object id) <ms-graph-client>`
* :ref:`GraphQL (for GraphQL based search) <graphql-client>`

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
   PurviewClient.update_entity_tags
   PurviewClient.delete_entity_tags