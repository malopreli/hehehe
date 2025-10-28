import streamlit as st
import requests
from typing import List, Dict

# ---------- Page setup ----------
st.set_page_config(page_title="YouTube Search (Minimal)", page_icon="🎬", layout="wide")
st.title("🎬 YouTube Search")
st.caption("Paste your YouTube Data API v3 key, enter a search query, and choose how many videos to display.")

# ---------- Inputs ----------
# Persist the API key during the session (so it doesn't clear on rerun)
if "yt_api_key" not in st.session_state:
    st.session_state.yt_api_key = ""

api_key = st.text_input("YouTube API Key", value=st.session_state.yt_api_key, type="password", help="You can create an API key in Google Cloud → APIs & Services.")
st.session_state.yt_api_key = api_key  # keep it in session

query = st.text_input("🔍 Search query", placeholder="e.g., machine learning tutorials")
max_results = st.number_input("Number of videos to display", min_value=1, max_value=50, value=12, step=1, help="YouTube API allows up to 50 results per request.")

search_clicked = st.button("Search", type="primary", use_container_width=True)

# ---------- Helpers ----------
def safe_get(d: Dict, path: List[str], default=None):
    """Safely get nested dict values."""
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
        # Optional: order by relevance (default) – you could also use "date", "viewCount", etc.
        "order": "relevance",
        # Safe search can be "none", "moderate", or "strict"
        "safeSearch": "moderate",
    }
    resp = requests.get(url, params=params, timeout=15)
    # Raise for non-2xx (so we can show a nice message below)
    resp.raise_for_status()
    return resp.json()

# ---------- Validation & Action ----------
if search_clicked:
    if not api_key:
        st.error("Please paste your **YouTube API key** to proceed.")
    elif not query.strip():
        st.error("Please enter a **search query**.")
    else:
        try:
            data = search_youtube(api_key, query.strip(), int(max_results))

            # Handle API-level errors (returned in JSON even with 200 OK sometimes)
            if "error" in data:
                code = safe_get(data, ["error", "code"], "Unknown")
                message = safe_get(data, ["error", "message"], "Unknown error.")
                st.error(f"API Error ({code}): {message}")
            else:
                items = data.get("items", [])
                if not items:
                    st.warning("No videos found. Try a different query or fewer filters.")
                else:
                    st.write(f"### Results for **{query}** ({len(items)})")
                    # Responsive grid: 1–4 columns depending on width
                    num_cols = 4
                    cols = st.columns(num_cols)

                    for i, item in enumerate(items):
                        video_id = safe_get(item, ["id", "videoId"], "")
                        snippet = item.get("snippet", {})
                        title = snippet.get("title", "Untitled")
                        channel = snippet.get("channelTitle", "Unknown channel")
                        # Pick the best available thumbnail
                        thumb = (
                            safe_get(snippet, ["thumbnails", "high", "url"]) or
                            safe_get(snippet, ["thumbnails", "medium", "url"]) or
                            safe_get(snippet, ["thumbnails", "default", "url"])
                        )
                        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

                        with cols[i % num_cols]:
                            if thumb:
                                st.image(thumb, use_container_width=True)
                            if url:
                                st.markdown(f"[**{title}**]({url})")
                            else:
                                st.write(f"**{title}**")
                            st.caption(f"by {channel}")

        except requests.HTTPError as http_err:
            # HTTP errors (e.g., 403 for invalid key / quota exceeded)
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

# ---------- Hints ----------
with st.expander("Need help getting an API key?", expanded=False):
    st.markdown(
        """
1. Go to **Google Cloud Console** → **APIs & Services**.
2. Create (or choose) a project.
3. **Enable APIs** → search for **YouTube Data API v3** and enable it.
4. Go to **Credentials** → **Create credentials** → **API key**.
5. Copy the key and paste it above.
        """
    )
