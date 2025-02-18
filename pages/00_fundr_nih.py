# pages/fundr.py

import streamlit as st
import os
import pandas as pd
from utilities.nih_data import load_nih_data, query_nih_data, get_unique_values as get_unique_values_nih
from ui.ui_fp import render_banner_nih, render_card_nih, render_cards_grid

# --- Import our podcast generation function ---
from utilities.ai_podcast import generate_podcast_audio

# --- Imports for Sumy summarization ---
from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

st.set_page_config(page_title="Fundr - NIH Dashboard", layout="wide")

# --- Helper functions for CSS loading ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def remote_css(url):
    st.markdown(f'<link href="{url}" rel="stylesheet">', unsafe_allow_html=True)

remote_css("https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css")
local_css("style.css")

def human_format(num):
    try:
        num = float(num)
    except:
        return num
    magnitude = 0
    while abs(num) >= 1000 and magnitude < 5:
        magnitude += 1
        num /= 1000.0
    suffix = ['', 'K', 'M', 'B', 'T', 'P'][magnitude]
    return f"{num:.2f}{suffix}"

# --- File path for NIH data ---
NIH_FILE_PATH = os.path.join("funddb", "NIH_data.csv")

st.title("Fundr: NIH Dashboard")

# Load NIH data (cached in session state)
if "duck_conn_nih" not in st.session_state:
    st.session_state["duck_conn_nih"] = load_nih_data(NIH_FILE_PATH)
conn = st.session_state["duck_conn_nih"]

# NIH search filters
title_search = st.sidebar.text_input("Search Title")
release_date_search = st.sidebar.text_input("Search Release Date")
activity_code_search = st.sidebar.text_input("Search Activity Code")
description_search = st.sidebar.text_input("Search Description")

try:
    parent_orgs = ['All'] + get_unique_values_nih(conn, "Parent_Organization")
    organizations = ['All'] + get_unique_values_nih(conn, "Organization")
    document_types = ['All'] + get_unique_values_nih(conn, "Document_Type")
except Exception as e:
    st.error(f"Error loading filter options: {e}")
    parent_orgs = ['All']
    organizations = ['All']
    document_types = ['All']

parent_org_filter = st.sidebar.selectbox("Filter by Parent Organization", options=parent_orgs)
organization_filter = st.sidebar.selectbox("Filter by Organization", options=organizations)
document_type_filter = st.sidebar.selectbox("Filter by Document Type", options=document_types)

df = query_nih_data(
    conn,
    title_search=title_search,
    release_date_search=release_date_search,
    activity_code_search=activity_code_search,
    parent_org_filter=parent_org_filter,
    organization_filter=organization_filter,
    document_type_filter=document_type_filter  # <-- Use the single selected value
)

# Filter by description after the query, if provided
if description_search and "Description" in df.columns:
    df = df[df["Description"].str.contains(description_search, case=False, na=False)]

# --- Build banner (scorecard) for NIH ---
total_docs = len(df)
unique_orgs = len(df['Organization'].dropna().unique())
unique_activity = len(df['Activity_Code'].dropna().unique())
banner_html = render_banner_nih(total_docs, unique_orgs, unique_activity)
st.markdown(banner_html, unsafe_allow_html=True)

# --- Additional CSS for 100% width audio container ---
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

# --- Generate and render cards for each NIH record with added functionality ---
cards = [render_card_nih(row) for _, row in df.iterrows()]
grid = render_cards_grid(cards, cards_per_row=3)

for row_cards, idx in zip(grid, range(0, len(df), 3)):
    cols = st.columns(len(row_cards))
    for col, card_html, real_index in zip(cols, row_cards, df.index[idx: idx+len(row_cards)]):
        with col:
            st.markdown(card_html, unsafe_allow_html=True)
            # Fetch the URL from the 'URL' column for summarization.
            url = df.loc[real_index, "URL"] if "URL" in df.columns else ""
            expand_key = f"desc_expanded_{real_index}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False

            bcol1, bcol2, bcol3 = st.columns(3)
            with bcol1:
                if st.button("Summarize", key=f"summarize_{real_index}"):
                    LANGUAGE = "english"
                    SENTENCES_COUNT = 10
                    try:
                        if not url:
                            st.error("No URL provided for summarization.")
                        else:
                            parser = HtmlParser.from_url(url, Tokenizer(LANGUAGE))
                            stemmer = Stemmer(LANGUAGE)
                            summarizer = Summarizer(stemmer)
                            summarizer.stop_words = get_stop_words(LANGUAGE)
                            summary_sentences = []
                            for sentence in summarizer(parser.document, SENTENCES_COUNT):
                                summary_sentences.append(str(sentence))
                            summary_text = " ".join(summary_sentences)
                            st.write("**Summary:**", summary_text)
                    except Exception as e:
                        st.error(f"Error during summarization: {e}")
            with bcol2:
                if not st.session_state[expand_key]:
                    if len(url) > 400:
                        if st.button("Expand", key=f"expand_button_{real_index}"):
                            st.session_state[expand_key] = True
                else:
                    st.write("**URL:**")
                    st.write(url)
            with bcol3:
                if st.button("FundrAI", key=f"fundrai_{real_index}"):
                    try:
                        LANGUAGE = "english"
                        SENTENCES_COUNT = 10
                        if not url:
                            st.error("No URL provided for summarization.")
                        else:
                            # Generate summary text from the URL using Sumy.
                            parser = HtmlParser.from_url(url, Tokenizer(LANGUAGE))
                            stemmer = Stemmer(LANGUAGE)
                            summarizer = Summarizer(stemmer)
                            summarizer.stop_words = get_stop_words(LANGUAGE)
                            summary_sentences = []
                            for sentence in summarizer(parser.document, SENTENCES_COUNT):
                                summary_sentences.append(str(sentence))
                            summary_text = " ".join(summary_sentences)
                            
                            row_dict = df.loc[real_index].to_dict()
                            # Pass the generated summary_text to the podcast generator.
                            audio_content = generate_podcast_audio(row_dict, summary_text=summary_text)
                            st.session_state[f'audio_{real_index}'] = audio_content
                            st.success("Podcast generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating audio: {e}")
                if f'audio_{real_index}' in st.session_state:
                    audio_content = st.session_state[f'audio_{real_index}']
                    st.audio(audio_content, format='audio/wav')

# --- Reset Database button ---
if st.sidebar.button("Reset Database"):
    if "duck_conn_nih" in st.session_state:
        del st.session_state["duck_conn_nih"]
    try:
        st.experimental_rerun()
    except Exception:
        st.write("Reset complete. Please refresh the page.")

if 'audio_{real_index}' in st.session_state:
    st.balloons()
