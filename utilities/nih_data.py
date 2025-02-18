# utilities/nih_data.py
import duckdb
import pandas as pd

def load_nih_data(file_path):
    """
    Loads the NIH CSV data from the given file path into an in-memory DuckDB table named 'nih'.
    Returns a DuckDB connection.
    """
    df = pd.read_csv(file_path)
    conn = duckdb.connect(database=':memory:')
    conn.execute("CREATE TABLE nih AS SELECT * FROM df")
    return conn

def query_nih_data(conn, title_search='', release_date_search='', activity_code_search='',
                   parent_org_filter='All', organization_filter='All', document_type_filter='All',
                   clinical_trials_search=''):
    """
    Queries the 'nih' table with optional filters.
      - title_search: case-insensitive keyword search on Title.
      - release_date_search: case-insensitive keyword search on Release_Date.
      - activity_code_search: case-insensitive keyword search on Activity_Code.
      - parent_org_filter: exact match on Parent_Organization.
      - organization_filter: exact match on Organization.
      - document_type_filter: exact match on Document_Type.
      - clinical_trials_search: case-insensitive keyword search on Clinical_Trials.
    Returns the result as a Pandas DataFrame.
    """
    sql = "SELECT * FROM nih WHERE 1=1"
    if title_search:
        sql += f" AND Title ILIKE '%{title_search}%'"
    if release_date_search:
        sql += f" AND Release_Date ILIKE '%{release_date_search}%'"
    if activity_code_search:
        sql += f" AND Activity_Code ILIKE '%{activity_code_search}%'"
    if parent_org_filter != 'All':
        sql += f" AND Parent_Organization = '{parent_org_filter}'"
    if organization_filter != 'All':
        sql += f" AND Organization = '{organization_filter}'"
    if document_type_filter != 'All':
        sql += f" AND Document_Type = '{document_type_filter}'"
    if clinical_trials_search:
        sql += f" AND Clinical_Trials ILIKE '%{clinical_trials_search}%'"
    return conn.execute(sql).fetchdf()

def get_unique_values(conn, column):
    """
    Returns a list of unique, non-null values for a given column from the 'nih' table.
    """
    query = f"SELECT DISTINCT {column} FROM nih WHERE {column} IS NOT NULL ORDER BY {column}"
    df = conn.execute(query).fetchdf()
    return df[column].tolist()
