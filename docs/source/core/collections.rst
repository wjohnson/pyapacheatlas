.. _collections-client:
==========================
PurviewCollectionsClient
==========================
.. currentmodule:: pyapacheatlas.core.collections

.. autosummary::
   :toctree: api/

   PurviewCollectionsClient

The PurviewCollectionsClient class supports creating and moving entities into
specific collections as per the `catalog data plane collections`_ and it
provides a subset of support for the `account data plane collections`_ APIs.

.. _catalog data plane collections: https://docs.microsoft.com/en-us/rest/api/purview/catalogdataplane/collection
.. _account data plane collections: https://docs.microsoft.com/en-us/rest/api/purview/accountdataplane/collections

.. autosummary::
   :toctree: api/

   PurviewCollectionsClient.upload_single_entity
   PurviewCollectionsClient.upload_entities
   PurviewCollectionsClient.move_entities
   PurviewCollectionsClient.list_collections
   PurviewCollectionsClient.create_or_update_collection
