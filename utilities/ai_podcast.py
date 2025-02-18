# utilities/ai_podcast.py

import os
import re
import json
import wave
import io

import streamlit as st  # Using st.secrets for credentials
import google.cloud.texttospeech as tts

# Import Gemini for content generation
from google import genai
from google.genai import types

from google.oauth2.service_account import Credentials

#############################################
# 1) Load Gemini / Google TTS credentials from st.secrets
#############################################

# 1A) Load Gemini API key from st.secrets
try:
    gemini_api_key = st.secrets["gemini"]["api_key"]
except (KeyError, AttributeError):
    raise ValueError("Gemini API key not found in st.secrets['gemini']['api_key']")

# 1B) Set up the Google Cloud TTS client using service account info from st.secrets["google_cloud"]
try:
    google_cloud_info = st.secrets["google_cloud"]
    # google_cloud_info is a dict containing the service account JSON keys
    credentials = Credentials.from_service_account_info(google_cloud_info)
    tts_client = tts.TextToSpeechClient(credentials=credentials)
except (KeyError, AttributeError):
    raise ValueError("Google Cloud credentials not found in st.secrets['google_cloud']")

#############################################
# 2) Load system prompt from prompt.json
#############################################

PROMPT_PATH = os.path.join("utilities", "prompt.json")
SYSTEM_INSTRUCTION = ""
if os.path.exists(PROMPT_PATH):
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as pf:
            data = json.load(pf)
        # Adjust the key to match your JSON – your file uses "system_prompt"
        SYSTEM_INSTRUCTION = data.get("system_prompt", "")
    except json.JSONDecodeError as je:
        raise ValueError(f"Invalid JSON in prompt.json: {je}")

#############################################
# 3) Gemini & TTS helper functions
#############################################

def load_gemini_client():
    """
    Configures and returns a Gemini client using the st.secrets API key.
    """
    client = genai.Client(api_key=gemini_api_key)
    return client

def estimate_audio_duration(text, speaking_rate=1.0):
    """Estimate duration (in minutes) for final TTS at ~150 words per minute."""
    wpm = 150
    word_count = len(text.split())
    return word_count / (wpm * speaking_rate)

def adjust_script_for_duration(text, target_minutes=1.0, speaking_rate=1.0):
    """
    If the generated script is longer than target_minutes at 150 wpm,
    truncate it to approximately meet the target.
    """
    current_duration = estimate_audio_duration(text, speaking_rate)
    if current_duration > target_minutes:
        words = text.split()
        max_words = int(target_minutes * 150 * speaking_rate)
        truncated = " ".join(words[:max_words]) + "..."
        return truncated
    return text

#############################################
# 4) Main podcast generation function
#############################################

def generate_podcast_audio(row_dict, summary_text=None):
    """
    1) Construct a prompt from row_dict (OpportunityTitle, Description, etc.)
       OR use the provided summary_text.
    2) Use Gemini LLM (with system instructions from prompt.json) to get a ~1-minute script.
    3) TTS that script with Google Cloud TTS, returning raw audio bytes (LINEAR16).
    """
    # 1) Build content from row_dict unless a summary is provided.
    if summary_text and summary_text.strip():
        content_str = summary_text
    else:
        title = row_dict.get("OpportunityTitle", "N/A")
        desc = row_dict.get("Description", "")
        close_date = row_dict.get("CloseDate", "")
        funding = row_dict.get("EstimatedTotalProgramFunding", "N/A")
        content_str = (
            f"Grant Title: {title}\n"
            f"Funding: {funding}\n"
            f"Close Date: {close_date}\n"
            f"Description:\n{desc}\n"
        )

    # 2) Use Gemini to generate a short, ~1-minute podcast script.
    gemini_client = load_gemini_client()

    config = types.GenerateContentConfig(
        max_output_tokens=500,  # Enough tokens for ~1 minute of speech
        temperature=0.3,
        top_k=40,
        top_p=0.95,
        system_instruction=SYSTEM_INSTRUCTION
    )

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[content_str],
            config=config
        )
        script = response.text
        if not script or not script.strip():
            raise RuntimeError("Gemini returned empty script.")

        # Simple post-processing: remove extraneous formatting.
        script = re.sub(r"\*+", "", script)       # Remove groups of asterisks
        script = re.sub(r"`{3,}", "", script)       # Remove triple backticks

        # Truncate script to ~1 minute duration.
        script = adjust_script_for_duration(script, target_minutes=1.0, speaking_rate=1.0)
    except Exception as e:
        raise RuntimeError(f"Error generating Gemini script: {e}")

    # 3) Synthesize speech with Google Cloud TTS.
    try:
        input_text = tts.SynthesisInput(text=script)
        voice_params = tts.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=tts.SsmlVoiceGender.FEMALE,
            name="en-US-Standard-C"
        )
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            pitch=0.0,
            sample_rate_hertz=16000
        )
        response = tts_client.synthesize_speech(
            request={"input": input_text, "voice": voice_params, "audio_config": audio_config}
        )
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(response.audio_content)
            return wav_buffer.getvalue()
    except Exception as e:
        raise RuntimeError(f"Audio generation error: {e}")
