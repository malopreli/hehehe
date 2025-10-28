import streamlit as st
import requests
from typing import List, Dict

# ---------- Page setup ----------
st.set_page_config(page_title="YouTube Search & Watch", page_icon="🎬", layout="wide")
st.title("🎬 YouTube Search & Watch")
st.caption("Paste your YouTube Data API v3 key, search a topic, set how many results to show, and watch videos inline.")

# ---------- Inputs ----------
if "yt_api_key" not in st.session_state:
    st.session_state.yt_api_key = ""

api_key = st.text_input(
    "YouTube API Key",
    value=st.session_state.yt_api_key,
    type="password",
    help="Create an API key in Google Cloud → APIs & Services → Credentials."
)
st.session_state.yt_api_key = api_key

query = st.text_input("🔍 Search query", placeholder="e.g., 'python tutorials for beginners'")
max_results = st.number_input(
    "Number of videos to display",
    min_value=1, max_value=50, value=9, step=1,
    help="YouTube API allows up to 50 results per request."
)

search_clicked = st.button("Search", type="primary", use_container_width=True)

# ---------- Helpers ----------
def safe_get(d: Dict, path: List[str], default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

def search_youtube(api_key: str, query: str, max_results: int) -> Dict:
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
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

# ---------- Action ----------
if search_clicked:
    if not api_key:
        st.error("Please paste your **YouTube API key** to proceed.")
    elif not query.strip():
        st.error("Please enter a **search query**.")
    else:
        try:
            data = search_youtube(api_key, query.strip(), int(max_results))

            if "error" in data:
                code = safe_get(data, ["error", "code"], "Unknown")
                message = safe_get(data, ["error", "message"], "Unknown error.")
                st.error(f"API Error ({code}): {message}")
            else:
                items = data.get("items", [])
                if not items:
                    st.warning("No videos found. Try a different query.")
                else:
                    st.write(f"### Results for **{query}** ({len(items)})")

                    # Layout: 3 videos per row for a good balance
                    cols_per_row = 3
                    cols = st.columns(cols_per_row)

                    for i, item in enumerate(items):
                        video_id = safe_get(item, ["id", "videoId"], "")
                        snippet = item.get("snippet", {})
                        title = snippet.get("title", "Untitled")
                        channel = snippet.get("channelTitle", "Unknown channel")

                        # You can pass either the watch URL or the embed URL; st.video supports both.
                        # We'll use the standard watch URL for simplicity.
                        watch_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

                        with cols[i % cols_per_row]:
                            # Title (no link)
                            st.markdown(f"**{title}**")
                            st.caption(f"by {channel}")
                            if watch_url:
                                st.video(watch_url)  # Plays inline inside the app
                            else:
                                st.info("This item is missing a playable video ID.")

        except requests.HTTPError as http_err:
            try:
                err_json = http_err.response.json()
                message = safe_get(err_json, ["error", "message"], str(http_err))
            except Exception:
                message = str(http_err)
            st.error(f"Request failed: {message}")

        except requests.RequestException as net_err:
            st.error(f"Network error: {net_err}")

        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ---------- Quick help ----------
with st.expander("How to get an API key", expanded=False):
    st.markdown(
        """
1. Go to **Google Cloud Console** → **APIs & Services**.
2. Create (or select) a project.
3. **Enable APIs** → search for **YouTube Data API v3** and enable it.
4. **Credentials** → **Create credentials** → **API key**.
5. Copy the key and paste it above.
        """
    )
