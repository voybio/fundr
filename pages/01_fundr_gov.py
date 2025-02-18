import streamlit as st
import os
import pandas as pd
from datetime import datetime, date
import tempfile  # For persistent temporary audio file storage

# Import summarize_text from grant_sumy, not from grants_data
from utilities.grant_sumy import summarize_text
from utilities.grants_data import (
    download_and_extract_xml,
    load_data_into_duckdb_from_memory,  # note new function
    query_grants,
    get_grant_status,
    top_10_agencies_by_budget,
    top_10_agencies_by_count
)
from utilities.ai_podcast import generate_podcast_audio
from ui.ui_gov import render_banner_grants, render_card_grants, render_cards_grid

from streamlit_advanced_audio import audix, WaveSurferOptions
import requests
import zipfile
import io

st.set_page_config(page_title="Fundr - Grants.Gov Dashboard", layout="wide")

def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)

remote_css("https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css")
local_css("style.css")

st.title("Fundr: Grants.Gov Dashboard")

# 1) Download XML data in memory if not in session_state
if "grants_xml_data" not in st.session_state:
    st.session_state["grants_xml_data"] = download_and_extract_xml(st)

if not st.session_state["grants_xml_data"]:
    st.error("No XML data found from the URL.")
    st.stop()

# 2) Load or reuse the database connection
if "grants_conn" not in st.session_state:
    st.session_state["grants_conn"] = load_data_into_duckdb_from_memory(st.session_state["grants_xml_data"])

conn = st.session_state["grants_conn"]

# --- SIDEBAR FILTERS ---
title_search = st.sidebar.text_input("Search Title (contains)", "")
id_search = st.sidebar.text_input("Search ID (contains)", "")
number_search = st.sidebar.text_input("Search Number (contains)", "")
agency_search = st.sidebar.text_input("Search Agency (contains)", "")
description_search = st.sidebar.text_input("Search Description (contains)", "")

status_options = ["Active", "Retired", "No close date", "All"]
status_choice = st.sidebar.selectbox("Status", status_options, index=0)

# 3) Query data
df_all = query_grants(
    conn,
    title_search=title_search,
    id_search=id_search,
    number_search=number_search,
    agency_search=agency_search,
    description_search=description_search
)

# 4) Filter by Active/Retired
df_all["GrantStatus"] = df_all["CloseDate"].apply(get_grant_status)
if status_choice != "All":
    df_all = df_all[df_all["GrantStatus"] == status_choice].copy()

# 5) Top 10 logic
if "top_10_mode" not in st.session_state:
    st.session_state["top_10_mode"] = None
if "selected_top_10_agencies" not in st.session_state:
    st.session_state["selected_top_10_agencies"] = []

colA, colB = st.columns(2)
if colA.button("Budget: Top 10"):
    st.session_state["top_10_mode"] = "budget"
    st.session_state["selected_top_10_agencies"] = []
if colB.button("Number: Top 10"):
    st.session_state["top_10_mode"] = "number"
    st.session_state["selected_top_10_agencies"] = []

top_10_agencies = []
if st.session_state["top_10_mode"] == "budget":
    top_df = top_10_agencies_by_budget(df_all)
    top_10_agencies = top_df["AgencyName"].tolist()
elif st.session_state["top_10_mode"] == "number":
    freq_df = top_10_agencies_by_count(df_all)
    top_10_agencies = freq_df["AgencyName"].tolist()

if top_10_agencies:
    chosen = st.multiselect(
        "Select any agencies to filter by:",
        top_10_agencies,
        default=st.session_state["selected_top_10_agencies"]
    )
    st.session_state["selected_top_10_agencies"] = chosen

if st.session_state["selected_top_10_agencies"]:
    df_all = df_all[df_all["AgencyName"].isin(st.session_state["selected_top_10_agencies"])].copy()

# 6) Banner
total_opps = len(df_all)
df_all["EstimatedTotalProgramFunding"] = pd.to_numeric(df_all["EstimatedTotalProgramFunding"], errors='coerce')
sum_funding = df_all["EstimatedTotalProgramFunding"].fillna(0).sum()
total_budget_str = f"${sum_funding:,.0f}" if sum_funding else ""
unique_agencies = df_all["AgencyName"].nunique(dropna=True) if "AgencyName" in df_all.columns else 0
banner_html = render_banner_grants(total_opps, unique_agencies, total_budget_str)
st.markdown(banner_html, unsafe_allow_html=True)

# 7) Pagination
PAGE_SIZE = 50
if "page_number" not in st.session_state:
    st.session_state.page_number = 0

col1, col2 = st.columns(2)
if col1.button("Previous Page"):
    st.session_state.page_number = max(0, st.session_state.page_number - 1)
if col2.button("Next Page"):
    if (st.session_state.page_number + 1) * PAGE_SIZE < len(df_all):
        st.session_state.page_number += 1

start_idx = st.session_state.page_number * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE

if start_idx >= len(df_all):
    st.session_state.page_number = 0
    start_idx = 0
    end_idx = PAGE_SIZE

df_page = df_all.iloc[start_idx:end_idx]
st.write(f"Showing results {start_idx+1} - {min(end_idx, len(df_all))} of {len(df_all)} total.")

# 8) Render cards & Summaries
cards = []
for i, row in df_page.iterrows():
    card_html = render_card_grants(row)
    cards.append(card_html)

grid = render_cards_grid(cards, cards_per_row=3)

wave_options = WaveSurferOptions(
    wave_color="#2B88D9",
    progress_color="#b91d47",
    height=120,
    bar_width=2,
    bar_gap=1
)

st.markdown(
    """
    <style>
    .audio-container {
      width: 100% !important;
      max-width: 100%;
      margin-top: 8px;
      margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

for row_cards, idxs in zip(grid, range(0, len(df_page), 3)):
    cols = st.columns(len(row_cards))
    for col, card_html, real_index in zip(cols, row_cards, df_page.index[idxs:idxs+len(row_cards)]):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)
            full_description = df_page.loc[real_index, "Description"] or ""
            expand_key = f"desc_expanded_{real_index}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False

            # Summarize, Expand, FundrAI
            bcol1, bcol2, bcol3 = st.columns(3)

            with bcol1:
                if st.button("Summarize", key=f"summarize_{real_index}"):
                    summary = summarize_text(full_description, sentence_count=10)
                    st.write("**Summary:**", summary)

            with bcol2:
                if not st.session_state[expand_key]:
                    if len(full_description) > 400:
                        if st.button("Expand", key=f"expand_button_{real_index}"):
                            st.session_state[expand_key] = True
                else:
                    st.write("**Full Description:**")
                    st.write(full_description)

            with bcol3:
                if st.button("FundrAI", key=f"fundrai_{real_index}"):
                    try:
                        row_dict = df_page.loc[real_index].to_dict()
                        audio_content = generate_podcast_audio(row_dict)
                        st.session_state[f'audio_{real_index}'] = audio_content
                        st.success("Podcast generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating audio: {e}")

                if f'audio_{real_index}' in st.session_state:
                    audio_content = st.session_state[f'audio_{real_index}']
                    st.audio(audio_content, format='audio/wav')

# 9) Reset Database
if st.sidebar.button("Reset Database"):
    if "grants_conn" in st.session_state:
        del st.session_state["grants_conn"]
    if "grants_xml_data" in st.session_state:
        del st.session_state["grants_xml_data"]
    st.session_state.page_number = 0
    st.experimental_rerun()

# insert the css below for overall look
st.markdown(
    """
    <style>
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f8f9fa;
        color: #343a40;
        margin: 0;
    }
    .block-container {
        max-width: 100%;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.1);
        margin: 1rem auto; /* Center the block container */
    }
    h1, h2, h3 {
        font-weight: 750;
        color: #007bff;
        text-align: center;
    }
    p, li {
        font-size: 1.1rem;
        line-height: 1.6;
    }
    a {
        color: #007bff;
        text-decoration: none;
    }
    a:hover {
        text-decoration: underline;
    }
    .element-container {
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.07);
        border-radius: 0.25rem;
        padding: 0.5rem;
        background-color: #fff;
        margin-bottom: 0.5rem; /* Add some spacing between elements */
    }
    .stButton>button {
        color: #fff;
        background-color: #007bff;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
        transition: background-color 0.3s ease;
        font-size: 1rem;
        display: block; /* Make buttons full width */
        width: 100%; /* Ensure full width */
        margin-bottom: 0.5rem; /* Add spacing below buttons */
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    audio {
        width: 100%;
        margin-top: 0.5rem;
    }
    /* Fix for overlapping elements */
    .stRadio, .stSelectbox, .stTextInput {
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)