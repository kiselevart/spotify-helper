import streamlit as st
import pandas as pd
import logging
import requests

# Import functions from other modules
from src.spotify_client import FEATURES_ENDPOINT, get_spotify_token, search_tracks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Streamlit UI Configuration ---
st.set_page_config(layout="wide")
st.title("Spotify Audio Features Analysis")

# Access Spotify configuration from Streamlit secrets
CLIENT_ID = st.secrets["spotify"]["CLIENT_ID"]
CLIENT_SECRET = st.secrets["spotify"]["CLIENT_SECRET"]
FEATURES_ENDPOINT = st.secrets["spotify"]["FEATURES_ENDPOINT"]
print(CLIENT_ID, CLIENT_SECRET)

# Initialize token in session state if not present
if "spotify_token" not in st.session_state:
    st.session_state.spotify_token = None

token = get_spotify_token(CLIENT_ID, CLIENT_SECRET)
if token:
    st.session_state.spotify_token = token
else:
    st.session_state.spotify_token = None
    st.error("Failed to get token. Check credentials.")

if st.session_state.spotify_token:
    st.success("Token is active.")
else:
    st.warning("Token not available. Please authenticate.")

# --- Track Search Section ---
st.header("Fetch Tracks")
search_query = st.text_input(
    "Enter a search query (e.g., artist, track, genre):", value="Discover"
)
search_limit = st.slider("Number of tracks to fetch (max 50):", 10, 50, 25)

if st.button("Fetch Tracks & Analyze"):
    token = st.session_state.get("spotify_token", None)

    if not token:
        st.error("Please enter your Spotify credentials and click 'Get Spotify Token' first.")
    elif not search_query:
        st.warning("Please enter a search query.")
    else:
        with st.spinner(f"Searching for '{search_query}'..."):
            tracks_raw = search_tracks(token, search_query, limit=search_limit)

        if not tracks_raw:
            st.warning("No tracks found for your query.")
        else:
            # Create DataFrame for track information
            df_tracks = pd.DataFrame([
                {
                    "id": track["id"],
                    "name": track["name"],
                    "artist": ", ".join(artist["name"] for artist in track["artists"]),
                    "album": track["album"]["name"]
                }
                for track in tracks_raw if track and track.get("id")
            ]).drop_duplicates(subset=["id"])

            st.subheader(f"📊 Fetched Tracks ({len(df_tracks)})")
            st.dataframe(df_tracks[["name", "artist", "album"]])

            track_ids = df_tracks["id"].tolist()

            # --- Audio Features Fetching ---
            if track_ids:
                track_ids_str = ",".join(track_ids)
                headers = {"Authorization": f"Bearer {token}"}
                params = {"ids": track_ids_str}
                with st.spinner("Fetching audio features..."):
                    try:
                        response = requests.get(FEATURES_ENDPOINT, headers=headers, params=params)
                        response.raise_for_status()
                        features_data = response.json().get("audio_features", [])
                        if features_data:
                            df_features = pd.DataFrame(features_data)
                            st.subheader("🎵 Audio Features")
                            st.dataframe(df_features.head())
                        else:
                            st.warning("No audio features found for the selected tracks.")
                    except Exception as e:
                        logger.error(f"Error fetching audio features: {e}")
                        st.error(f"Error fetching audio features: {e}")