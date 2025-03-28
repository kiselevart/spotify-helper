import base64
import logging
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

SPOTIFY_ACCOUNT_URL = st.secrets["spotify"]["ACCOUNT_URL"]
SEARCH_ENDPOINT = st.secrets["spotify"]["SEARCH_ENDPOINT"]
FEATURES_ENDPOINT = st.secrets["spotify"]["FEATURES_ENDPOINT"]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spotify_token(client_id: str, client_secret: str) -> Optional[str]:
    """
    Fetches the Spotify access token using Client Credentials.

    Args:
        client_id: Your Spotify application's client ID.
        client_secret: Your Spotify application's client secret.

    Returns:
        The access token string, or None if an error occurred.
    """
    if not client_id or not client_secret:
        logger.error("Client ID or Client Secret not provided.")
        return None

    try:
        auth_str = f"{client_id}:{client_secret}"
        b64_auth_str = base64.b64encode(auth_str.encode()).decode()
        headers = {"Authorization": f"Basic {b64_auth_str}"}
        data = {"grant_type": "client_credentials"}

        response = requests.post(SPOTIFY_ACCOUNT_URL, data=data, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors

        token_info = response.json()
        access_token = token_info.get("access_token")
        if not access_token:
            logger.error("Access token not found in response.")
            st.error("Could not retrieve access token from Spotify response.")
            return None

        logger.info("Successfully obtained Spotify token.")
        return access_token

    except requests.exceptions.RequestException as e:
        logger.error(f"Error obtaining Spotify token: {e}")
        st.error(f"Network or API error obtaining token: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during token retrieval: {e}")
        st.error("An unexpected error occurred. Check logs.")
        return None


def search_tracks(token: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Searches for tracks on Spotify.

    Args:
        token: Spotify API access token.
        query: The search query string.
        limit: The maximum number of tracks to return (capped at 50).

    Returns:
        A list of track dictionaries, or an empty list if an error occurs or no results are found.
    """
    if not token:
        st.error("Invalid or missing Spotify token.")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "type": "track", "limit": min(limit, 50)}  # API limit is 50

    try:
        response = requests.get(SEARCH_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        tracks = data.get("tracks", {}).get("items", [])
        logger.info(f"Found {len(tracks)} tracks for query: '{query}'")
        return tracks

    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching tracks: {e}")
        st.error(f"API error during track search: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during track search: {e}")
        st.error("An unexpected error occurred during track search.")
        return []
