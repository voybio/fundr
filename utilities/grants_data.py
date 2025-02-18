# utilities/grants_data.py

import duckdb
import pandas as pd
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import requests
import zipfile
import io
import os
import streamlit as st

def parse_xml(xml_source):
    """
    Dynamically parses the XML, removing namespaces so that tags like
    '{http://apply.grants.gov/system/OpportunityDetail-V1.0}OpportunityID'
    become simply 'OpportunityID'.
    """
    tree = ET.parse(xml_source)
    root = tree.getroot()

    def strip_ns(tag):
        return re.sub(r'{.*}', '', tag)

    # Strip namespaces in the entire XML
    for elem in root.iter():
        elem.tag = strip_ns(elem.tag)

    records = []
    for parent in root.iter():
        opp_id_elem = parent.find('.//OpportunityID')
        if opp_id_elem is not None:
            record = {}
            for child in parent:
                tag_name = child.tag
                value = child.text.strip() if child.text else None

                # If repeated tag, store in a list
                if tag_name in record:
                    if isinstance(record[tag_name], list):
                        record[tag_name].append(value)
                    else:
                        record[tag_name] = [record[tag_name], value]
                else:
                    record[tag_name] = value
            records.append(record)

    return records

def load_data_into_duckdb_from_memory(xml_data):
    """
    Loads XML data (bytes) into an in-memory DuckDB table named 'grants'.
    Returns the DuckDB connection.
    Raises ValueError if no records are found.
    """
    # Parse in memory using BytesIO
    with io.BytesIO(xml_data) as buffer:
        records = parse_xml(buffer)

    if not records:
        raise ValueError("No records found in XML data (bytes).")

    df = pd.DataFrame(records)
    df.dropna(how="all", inplace=True)

    conn = duckdb.connect(database=':memory:')
    conn.execute("CREATE TABLE grants AS SELECT * FROM df")
    return conn

def query_grants(conn,
                 title_search='',
                 id_search='',
                 number_search='',
                 agency_search='',
                 description_search=''):
    sql = "SELECT * FROM grants WHERE 1=1"

    if title_search:
        sql += f" AND OpportunityTitle ILIKE '%{title_search}%'"
    if id_search:
        sql += f" AND OpportunityID ILIKE '%{id_search}%'"
    if number_search:
        sql += f" AND OpportunityNumber ILIKE '%{number_search}%'"
    if agency_search:
        sql += f" AND AgencyName ILIKE '%{agency_search}%'"
    if description_search:
        sql += f" AND Description ILIKE '%{description_search}%'"

    return conn.execute(sql).fetchdf()

def get_unique_values(conn, column):
    query = f"SELECT DISTINCT {column} FROM grants WHERE {column} IS NOT NULL ORDER BY {column}"
    df = conn.execute(query).fetchdf()
    return df[column].tolist()

def get_grant_status(close_date_str):
    if not close_date_str:
        return "No close date"
    try:
        close_dt = datetime.strptime(close_date_str, "%m%d%Y")
        now = datetime.now()
        return "Retired" if close_dt < now else "Active"
    except ValueError:
        return "No close date"

def top_10_agencies_by_budget(df):
    df["AwardCeiling"] = pd.to_numeric(df["AwardCeiling"], errors='coerce')
    df["EstimatedTotalProgramFunding"] = pd.to_numeric(df["EstimatedTotalProgramFunding"], errors='coerce')
    df["TotalBudget"] = df["AwardCeiling"].fillna(0) + df["EstimatedTotalProgramFunding"].fillna(0)
    grouped = df.groupby('AgencyName')["TotalBudget"].sum().reset_index()
    return grouped.sort_values("TotalBudget", ascending=False).head(10)

def top_10_agencies_by_count(df):
    freq_df = df["AgencyName"].value_counts().reset_index()
    freq_df.columns = ["AgencyName", "Frequency"]
    return freq_df.head(10)

def download_and_extract_xml(st, grants_xml_data=None):
    """
    Downloads and extracts the Grants.gov XML data from a zip file, returning bytes.

    Args:
        st: Streamlit object for UI elements.
        grants_xml_data (bytes, optional): If already available, pass it.
    Returns:
        bytes: The raw XML data or None if an error occurred.
    """
    if grants_xml_data:
        # If we somehow already have bytes, return them
        return grants_xml_data

    # Otherwise attempt to download from the URL
    today = datetime.today().strftime("%Y%m%d")
    zip_url = f"https://prod-grants-gov-chatbot.s3.amazonaws.com/extracts/GrantsDBExtract{today}v2.zip"

    try:
        response = requests.get(zip_url)
        response.raise_for_status()

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        # Assuming there's only one XML file
        xml_file_name = [name for name in zip_file.namelist() if name.endswith(".xml")][0]

        with zip_file.open(xml_file_name) as source:
            xml_data = source.read()

        st.success(f"Successfully downloaded XML from {zip_url} without saving locally.")
        return xml_data

    except requests.exceptions.RequestException as e:
        st.error(f"Error downloading XML from {zip_url}: {e}")
    except zipfile.BadZipFile:
        st.error(f"Error: Could not open the zip file from {zip_url}. It may not be valid.")
    except IndexError:
        st.error(f"Error: No XML file found inside the zip archive at {zip_url}.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    return None
