# utilities/sumy_punkt.py
import nltk
import os

# Use src/nltk_data as the NLTK data directory
NLTK_DATA_PATH = os.path.join(os.getcwd(), "src", "nltk_data")

# Ensure the directory exists
os.makedirs(NLTK_DATA_PATH, exist_ok=True)

# Set environment variable for NLTK
os.environ["NLTK_DATA"] = NLTK_DATA_PATH

# List of required NLTK resources
nltk_resources = ["punkt"]

# Download resources if not found
for resource in nltk_resources:
    try:
        nltk.data.find(f"tokenizers/{resource}")
    except LookupError:
        nltk.download(resource, download_dir=NLTK_DATA_PATH)
