import mysql.connector as mysqlConnector
import os
import json
import time

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasEntity, AtlasProcess

MYSQL_SERVER_HOSTNAME = os.environ.get('MYSQL_SERVER_HOSTNAME','')
MYSQL_INSTANCE_PORT = os.environ.get('MYSQL_INSTANCE_PORT', '')
MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', '')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_SERVERINSTANCE_CLOUDORONPREM = os.environ.get('MYSQL_SERVERINSTANCE_CLOUDORONPREM','')
MYSQL_SERVERINSTANCE_PROD_OR_OTHER = os.environ.get('MYSQL_SERVERINSTANCE_PROD_OR_OTHER','')
MYSQL_SERVERINSTANCE_CONTACTINFO = os.environ.get('MYSQL_SERVERINSTANCE_CONTACTINFO','')
MYSQL_SERVERINSTANCE_COMMENT = os.environ.get('MYSQL_SERVERINSTANCE_COMMENT','')
MYSQL_INCLUDE_DATABASES = os.environ.get('MYSQL_INCLUDE_DATABASES','')

class AtlasMySQL:
  guid_count = 0
  instance = None
  dbs = []
  db_tables = []
  table_columns = []

  def add_atlas_instance(self, version, instance_fqn):
    self.guid_count -= 1
    self.instance = AtlasEntity(
      name = f'MySQL v.{version}',
      typeName = 'pyapacheatlas_mysql_instance',
      qualified_name = instance_fqn,
      guid = self.guid_count,
      attributes = {
        'hostname': MYSQL_SERVER_HOSTNAME,
        'port': MYSQL_INSTANCE_PORT,
        'cloudOrOnPrem': MYSQL_SERVERINSTANCE_CLOUDORONPREM,
        'contact_info': MYSQL_SERVERINSTANCE_CONTACTINFO,
        'comment': MYSQL_SERVERINSTANCE_COMMENT
      }
    )

  def add_atlas_db(self, database, database_fqn):
    self.guid_count -= 1
    db = AtlasEntity(
      name = database[0],
      typeName = 'pyapacheatlas_mysql_db',
      qualified_name = database_fqn,
      guid = self.guid_count
    )
    self.dbs.append(db)
    return db

  def add_atlas_table(self, table, table_fqn):
    self.guid_count -= 1
    db_table = AtlasEntity(
      name = table[0],
      typeName = 'pyapacheatlas_mysql_table',
      qualified_name = table_fqn,
      guid = self.guid_count
    )
    self.db_tables.append(db_table)
    return db_table

  def add_atlas_column(self, column, table_fqn):
    self.guid_count -= 1
    column_fqn = f'{table_fqn}#{column.Field}'
    table_column = AtlasEntity(
      name = column.Field,
      typeName = 'pyapacheatlas_mysql_column',
      qualified_name = column_fqn,
      guid = self.guid_count,
      attributes = {
        'comment': self._decode_field_if_bytes(column.Comment),
        'data_type': self._decode_field_if_bytes(column.Type),
        'default_value': self._decode_field_if_bytes(column.Default),
        'isNullable': self._decode_field_if_bytes(column.Null),
        'isPrimaryKey': self._decode_field_if_bytes(column.Key) != None,
        'collation': self._decode_field_if_bytes(column.Collation)
      }
    )
    self.table_columns.append(table_column)
    return table_column

  def _decode_field_if_bytes(self, field):
    if not (field is None):
      if isinstance(field, bytes):
        return field.decode('utf-8')
      else:
        return str(field)
    else:
      return ''

def scan_meta_data(atlas_mysql):
    conn = mysqlConnector.connect(host = MYSQL_SERVER_HOSTNAME,
        user = MYSQL_USERNAME,
        passwd = MYSQL_PASSWORD
        )
    if conn:
        print('Connection Successful :)')
    else:
        print('Connection Failed :(')
    scan_server_instance(conn, atlas_mysql)
    conn.close()

def save_entities(atlas_mysql):
    oauth = ServicePrincipalAuthentication(
        tenant_id = os.environ.get('AZURE_TENANT_ID', ''),
        client_id = os.environ.get('AZURE_CLIENT_ID', ''),
        client_secret = os.environ.get('AZURE_CLIENT_SECRET', '')
        )
    client = PurviewClient(
        account_name = os.environ.get('PURVIEW_CATALOG_NAME', ''),
        authentication = oauth
        )
    entities = []
    entities.append(atlas_mysql.instance)
    for db in atlas_mysql.dbs:
        entities.append(db)
    for table in atlas_mysql.db_tables:
        entities.append(table)
    for column in atlas_mysql.table_columns:
        entities.append(column)

    assignments = client.upload_entities(entities)['guidAssignments']
    f = open(f"entities.{time.time()}.txt", "a")
    for guid in assignments:
        f.write(assignments[guid] + "\n")
    f.close()

def scan_server_instance(conn, atlas_mysql):
    instance_fqn = f'mysql://{MYSQL_SERVER_HOSTNAME}/'
    cursor = conn.cursor()
    cursor.execute("show variables like '%version';")
    mysql_vars = cursor.fetchall()
    version = next(version for (variable, version) in mysql_vars
        if variable == 'version')
    atlas_mysql.add_atlas_instance(version, instance_fqn)
    scan_databases(conn, atlas_mysql)

def scan_databases(conn, atlas_mysql):
    cursor = conn.cursor()
    cursor.execute('SHOW DATABASES;')
    databases = cursor.fetchall()
    for database in databases:
        if database[0] in MYSQL_INCLUDE_DATABASES:
            print(f'{database[0]} is included')
            database_fqn = f'{atlas_mysql.instance.qualifiedName}{database[0]}/'
            db = atlas_mysql.add_atlas_db(database, database_fqn)
            db.addRelationship(instance = atlas_mysql.instance)
            scan_tables(conn, atlas_mysql, db)
        else:
            print(f'{database[0]} is excluded')

def scan_tables(conn, atlas_mysql, atlas_database):
    cursor = conn.cursor()
    cursor.execute(f'show tables from {atlas_database.name};')
    tables = cursor.fetchall()
    for table in tables:
        table_fqn = f'{atlas_database.qualifiedName}{table[0]}'
        atlas_table = atlas_mysql.add_atlas_table(table, table_fqn)
        atlas_table.addRelationship(database = atlas_database)
        scan_columns(conn, atlas_mysql, atlas_database.name, atlas_table)

def scan_columns(conn, atlas_mysql, database, atlas_table):
    cursor = conn.cursor(named_tuple = True)
    cursor.execute(f'use {database};')
    cursor.execute(f'show full columns from {atlas_table.name};')
    results = cursor.fetchall()
    for result in results:
        tableColumn = atlas_mysql.add_atlas_column(result, atlas_table.qualifiedName)
        tableColumn.addRelationship(table = atlas_table)

if __name__ == '__main__':
    atlas_mysql = AtlasMySQL()
    scan_meta_data(atlas_mysql)
    save_entities(atlas_mysql)
