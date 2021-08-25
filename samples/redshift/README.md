### Sample to Export Redshift Metadata and Create Custom entites in Purview

- Install and configure ODBC drivers for Redshift from [here](https://docs.aws.amazon.com/redshift/latest/mgmt/configure-odbc-connection.html)

- Update `REDSHIFT_CONNECTION_STRING` details in [import_redshift_custom.py](import_redshift_custom.py)

- `pip install pyodbc`
- `pip install pandas`

- `python .\import_redshift_custom.py` 



![search](search-img-1.png)

![search](search-img-2.png)

![search](search-img-3.png)