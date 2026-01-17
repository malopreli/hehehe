import streamlit as st
import requests
from typing import List, Dict
import json 
# ---------- CONFIGURATION ----------
st.set_page_config(page_title="🎬 YouTube Search & Watch", page_icon="🎥", layout="wide")

# ✅ Your YouTube Data API key (replace with your own)
API_KEY = "AIzaSyCRoCfLINI3kMcvvSbMq6sISWnxiOUC4CQ"


# ---------- PAGE HEADER ----------
st.title("🎬 YouTube Search & Watch")
st.caption("Search YouTube videos directly and watch them here — no need to leave the app!")

# ---------- USER INPUTS ----------
query = st.text_input("🔍 Search query", placeholder="e.g., relaxing piano music")
max_results = st.number_input(
    "Number of videos to display",
    min_value=1, max_value=50, value=9, step=1,
    help="YouTube API allows up to 50 results per request."
)
search_clicked = st.button("Search", type="primary", use_container_width=True)

# ---------- HELPER FUNCTIONS ----------
def save_first_result(data: Dict, filename: str = "first_youtube_result.json") -> bool:
    """Save ONLY the first YouTube search result to a local JSON file."""
    items = data.get("items", [])
    if not items:
        return False

    first_item = items[0]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(first_item, f, indent=2)

    return True

def load_first_result(filename: str = "first_youtube_result.json") -> Dict:
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_get(d: Dict, path: List[str], default=None):
    """Safely access nested dictionary keys."""
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def search_youtube(api_key: str, query: str, max_results: int) -> Dict:
    """Perform a YouTube search using Data API v3."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": api_key,
        "order": "relevance",
        "safeSearch": "moderate",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()
    
# ---------- SEARCH LOGIC ----------
if search_clicked:
    if not query.strip():
        st.error("Please enter a **search query**.")
    else:
        try:
            data = search_youtube(API_KEY, query.strip(), int(max_results))

            # Save ONLY the first result to disk
            saved = save_first_result(data)

            if not saved:
                st.warning("No videos found. Try a different query.")
                st.stop()

            # Load the first result from disk
            first_item = load_first_result()
            video_id = safe_get(first_item, ["id", "videoId"], "")
            snippet = first_item.get("snippet", {})
            title = snippet.get("title", "Untitled")
            channel = snippet.get("channelTitle", "Unknown channel")

            watch_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

            st.write(f"### First Result for **{query}**")
            st.markdown(f"**{title}**")
            st.caption(f"by {channel}")

            if watch_url:
                st.video(watch_url)
            else:
                st.info("Video unavailable.")

        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ---------- FOOTER ----------
st.markdown("---")
st.caption("Built with ❤️ using Streamlit and the YouTube Data API v3.")

