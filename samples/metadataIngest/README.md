# Custom Metadata Ingestion for MySQL

## Introduction

This sample will provide a example of extracting metadata from a MySQL instance
and add assets to an Azure Purview catalog. Included in the setup is a local
instance of MySQL running in a Docker container with a sample Open dataset for
world data.

## Prerequisites

Python 3.6 or higher
Docker (if using the MySQL instance)
Azure Purview account
Azure Service Principal with Data Curator privileges to Azure Purview account

## Required Environment Variable settings

Use the following code to set the environment for Python to run

``` bash
export MYSQL_SERVER_HOSTNAME=<localhost or ipaddress>
export MYSQL_INSTANCE_PORT=<port>
export MYSQL_USERNAME=<username>
export MYSQL_PASSWORD=<password>
export MYSQL_INCLUDE_DATABASES=<comma separated list of databases to include>
export MYSQL_SERVERINSTANCE_CLOUDORONPREM=<onprem or cloud>
export MYSQL_SERVERINSTANCE_PROD_OR_OTHER=<dev, qa, prod, etc.>
export MYSQL_SERVERINSTANCE_CONTACTINFO=<contactinfo>
export MYSQL_SERVERINSTANCE_COMMENT=<comment for mysql instance>
export AZURE_CLIENT_ID=<service principal id>
export AZURE_CLIENT_SECRET=<service principal secret>
export AZURE_TENANT_ID=<aad tenant id>
export PURVIEW_CATALOG_NAME=<name of Azure Purview Account>
```

## Setting up Sample MySQL World Data

The following commands should configure a simple MySQL instance running on your
local machine and load and install the `world.sql` data.

Create a local network to have access to the MySQL container once started

``` bash
docker network create mysqlnet
```

Download and run the MySQL image and start the mysql daemon exposing MySQL on
port 3306.

``` bash
docker run --name mysqllocal -p 3306:3306  --network mysqlnet -e MYSQL_ROOT_PASSWORD=$MYSQL_PASSWORD -d  mysql
```

Connect to MySQL and grant permissions

``` bash
docker run -it --rm --network mysqlnet mysql mysql -hmysqllocal -p$MYSQL_PASSWORD
```

At the `mysql>` prompt, execute the following script to use unix socket authentication

``` sql
ALTER USER 'root' IDENTIFIED WITH mysql_native_password BY 'password';
flush privileges;
```

Connect and run the `world.sql` script to import the data into the MySQL instance

``` bash
docker exec -i mysqllocal sh -c 'exec mysql -uroot -ppassword' < world.sql
```

None of the sample data has comments, so for this sample, we will need to update
a table with a comment. Log in to MySQL with the following

``` bash
docker run -it --rm --network mysqlnet mysql mysql -hmysqllocal -p$MYSQL_PASSWORD
```

At the `mysql>` prompt, execute the following script to add a comment to the `city`
table

``` sql
ALTER TABLE city CHANGE id id int not null COMMENT "id of city";
```

## Running the Entity Registration script for MySQL

From the command prompt, run the `register_typedef.py`. The result will upload the Custom type 
definitions for our MySQL Instance > Database > Table > Column, as well as the relationship between them
defined in `pyapacheatlas_mysql_typedefs_v2.json`

Once the relationships are defined, we're ready to scan our MySQL Instance and ingest the metadata.

## Running the Custom Ingestion script for MySQL

From the command prompt, run the `mysql_metadata_ingest.py`. The result should show
a successful connection to MySQL and any tables that were excluded. If successful,
the output will also include the GUIDs of all entities that were cataloged. The
format of the output is to make it convenient to copy into the `installtypedef.http`
file for clean up after running the sample.
