.. _ms-graph-client:
==========================
Microsoft Graph Utilities
==========================
.. currentmodule:: pyapacheatlas.core.msgraph

.. autosummary::
   :toctree: api/

   MsGraphClient
   MsGraphException

The MSGraphClient provides utility functions to the MS Graph API. Specifically,
it includes methods to convert things you know (like your User Principal Name
(UPN)) or email address to an Azure Active Directory object id.

This is most useful for populating Microsoft Purview Experts and Owners since
they expect object ids.

In addition, the reader methods provide a parameter called `contacts_func` which
takes in a function as the argument. That function is called on every expert or
owner provided in the template upload.

.. autosummary::
   :toctree: api/

   MsGraphClient.upn_to_id
   MsGraphClient.email_to_id
   