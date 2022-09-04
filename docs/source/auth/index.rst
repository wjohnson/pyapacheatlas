==============
Authentication
==============

PyApacheAtlas provides three ways of authenticating.

* Using Azure Credential from the `azure-identity` package for Microsoft Purview.
    * This supports using managed identities, Azure CLI, and Interactive Auth as well.
* Using a Service Principal for Microsoft Purview.
* Using basic auth for Apache Atlas servers.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   azcredential
   serviceprincipal
   basic
   base
