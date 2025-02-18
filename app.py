# app.py
import streamlit as st
import utilities.sumy_punkt  # Import the sumy_punkt script

st.set_page_config(page_title="Fundr App", layout="wide")
st.title("Welcome to Fundr - Grants.Gov Dashboard")

st.write(
    """
    ### 🌟 Your Gateway to Grants and Research Funding

    Welcome to Fundr, an experimental platform for discovering grant opportunities. Whether you're a researcher, non-profit, or academic institution, Fundr simplifies the process of finding the funding you need.

    **Explore Our Key Features:**

    - 📋 **Comprehensive Grant Listings:** Access an extensive database of grants from various sources, all in one convenient location.
    - 🔍 **Customized Search:** Filter grants based on your specific criteria such as description, agency and eligibility requirements.
    - ⏰ **Real-time Updates:** Stay informed with the latest grant announcements and deadlines.
    - 📝 **Summaries:** Both textual and audio summaries are available for grant announcements.

     **Caution:** Fundr will fetch the database in real-time. This may take a few minutes. Please be patient.


    **Get Started Today:**
    - Some funding institutions: 
        - 🏛️ National Science Foundation (NSF)
        - 🏥 National Institutes of Health (NIH)
        - ⚡ Department of Energy (DOE)
        - 🛡️ Department of Defense (DOD)
        - 🚀 National Aeronautics and Space Administration (NASA)
        and many more...

    Use the sidebar to navigate to the dashboard:

    - **Fundr_NIH**: All current and available grants from the National Institutes of Health.
    - **Fundr_Gov**: Explore the Grants.gov dashboard and generate insightful summaries.
    

    Fundr is here to empower you with the resources you need to succeed. Start exploring now and unlock your funding potential!
    """
)


st.markdown(
    """
    <style>
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #f8f9fa;
        color: #343a40;
    }
    .block-container {
        max-width: 900px;
        margin: 3rem auto;
        padding: 2rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.05);
    }
    h1, h2, h3 {
        font-weight: 500;
        color: #007bff;
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
    </style>
    """,
    unsafe_allow_html=True
)
