### Sample to Export Snowflake Metadata and Create Custom entities in Purview

- Install and configure ODBC drivers for Snowflake from [here](https://sfc-repo.snowflakecomputing.com/odbc/index.html)

- Rename and update Snowflake connection details in `config.ini.example`

- Install Python needed libraries by running
  - `pip install -r requirements.txt -v`

- In case of issues installing PyODBC showing the error: `Microsoft Visual C++ 14.0 or greater is required` remember that instead of installing ~6GB of Microsoft tooling you can just download and install the compiled version [PyODBC](https://pypi.org/project/pyodbc/#files)
  - `pip install pyodbc-4.0.32-cp310-cp310-win_amd64.whl`

- Run with the command:
  - `python import_snowflake_custom.py`
