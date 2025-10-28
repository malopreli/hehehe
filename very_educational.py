# app.py
import streamlit as st
import requests
import math
import time
from datetime import datetime

st.set_page_config(page_title=" youtube For You", layout="wide")
st.markdown(
    """
    <style>
    /* Dark YouTube-like look (no copyrighted assets) */
    .stApp { background-color: #0f0f0f; color: #ffffff; }
    .header { text-align:center; padding: 10px 0; }
    .video-card { background: #151515; border-radius: 10px; padding: 10px; margin-bottom: 12px; }
    .video-thumb { border-radius: 8px; }
    .meta { color: #bdbdbd; font-size: 13px; }
    .title { font-weight:600; font-size:16px; margin-bottom:6px; color:#fff; }
    .desc { color:#cfcfcf; font-size:13px; }
    .shorts-thumb { border-radius:12px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='header'><h1>🎬 The Main One — For You</h1><p style='color:#bbb;margin-top:-8px'>Close to the real thing — powered by YouTube Data API</p></div>", unsafe_allow_html=True)
st.markdown("---")

# ------------------------------
# CONFIG - fill these before running
# ------------------------------
API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")  # recommended: put into Streamlit Secrets
# Fallback: you can directly paste your API key as a string (not recommended for public repos)
if not API_KEY:
    API_KEY = st.text_input("Enter your YouTube API Key (or set YOUTUBE_API_KEY in Streamlit Secrets)", type="password")

# Put the Calus Box channel ID here (or a channel username — helper below can convert)
CHANNEL_ID_OR_NAME = st.text_input("Channel ID or username (example: UC_x5XG1OV2P6uZZ5FSM9Ttw)", value="") 

# Choose how many videos to fetch per "page"
PAGE_SIZE = st.sidebar.slider("Videos per load", min_value=6, max_value=24, value=12, step=6)

st.sidebar.markdown("## Feed selectors")
show_shorts = st.sidebar.checkbox("Include 'Life Story' Shorts", value=True)
shorts_query = st.sidebar.text_input("Shorts search query", value="life story")

# ------------------------------
# Helper functions for YouTube Data API
# ------------------------------
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

def get_channel_id_from_username(username):
    """
    Convert a legacy username (if provided) to channelId.
    If already channel ID (starts with 'UC') return as-is.
    """
    username = username.strip()
    if username.startswith("UC"):
        return username
    # try search by forUsername
    params = {"part": "id", "forUsername": username, "key": API_KEY}
    r = requests.get(f"{YOUTUBE_API_BASE}/channels", params=params)
    data = r.json()
    if "items" in data and len(data["items"]) > 0:
        return data["items"][0]["id"]
    # try search by channel name
    params = {"part": "snippet", "q": username, "type": "channel", "key": API_KEY, "maxResults": 1}
    r = requests.get(f"{YOUTUBE_API_BASE}/search", params=params)
    data = r.json()
    if "items" in data and len(data["items"]) > 0:
        return data["items"][0]["snippet"]["channelId"]
    return None

def get_uploads_playlist_id(channel_id):
    params = {"part": "contentDetails", "id": channel_id, "key": API_KEY}
    r = requests.get(f"{YOUTUBE_API_BASE}/channels", params=params)
    data = r.json()
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_playlist_items(playlist_id, page_token=None, max_results=50):
    params = {
        "part": "snippet,contentDetails",
        "playlistId": playlist_id,
        "key": API_KEY,
        "maxResults": max_results
    }
    if page_token:
        params["pageToken"] = page_token
    r = requests.get(f"{YOUTUBE_API_BASE}/playlistItems", params=params)
    return r.json()

def fetch_video_stats(video_ids):
    # video_ids: list of ids
    if not video_ids:
        return {}
    params = {
        "part": "statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": API_KEY,
        "maxResults": 50
    }
    r = requests.get(f"{YOUTUBE_API_BASE}/videos", params=params)
    data = r.json()
    stats = {}
    for item in data.get("items", []):
        stats[item["id"]] = item
    return stats

def fetch_search_short_videos(query, page_token=None, max_results=25):
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "videoDuration": "short",
        "order": "date",  # recent shorts
        "maxResults": max_results,
        "key": API_KEY
    }
    if page_token:
        params["pageToken"] = page_token
    r = requests.get(f"{YOUTUBE_API_BASE}/search", params=params)
    return r.json()

# ------------------------------
# Session state for infinite scroll/pagination
# ------------------------------
if "uploads_playlist_id" not in st.session_state:
    st.session_state.uploads_playlist_id = None
if "playlist_page_token" not in st.session_state:
    st.session_state.playlist_page_token = None
if "videos" not in st.session_state:
    st.session_state.videos = []
if "shorts" not in st.session_state:
    st.session_state.shorts = []
if "loading" not in st.session_state:
    st.session_state.loading = False

# ------------------------------
# Initialize channel / playlist
# ------------------------------
if st.button("Load channel"):
    if not API_KEY:
        st.error("Please provide an API key first.")
    else:
        channel_id = get_channel_id_from_username(CHANNEL_ID_OR_NAME) if CHANNEL_ID_OR_NAME else None
        if not channel_id:
            st.error("Could not find channel ID for that input. Try pasting the channel ID (starts with 'UC...').")
        else:
            st.session_state.uploads_playlist_id = get_uploads_playlist_id(channel_id)
            st.session_state.playlist_page_token = None
            st.session_state.videos = []
            st.session_state.shorts = []
            st.experimental_rerun()

# ------------------------------
# Fetch next page of videos (uploads)
# ------------------------------
def load_next_videos():
    if not st.session_state.uploads_playlist_id:
        return
    st.session_state.loading = True
    resp = fetch_playlist_items(st.session_state.uploads_playlist_id, page_token=st.session_state.playlist_page_token, max_results=PAGE_SIZE)
    items = resp.get("items", [])
    # extract videoIds
    ids = [it["contentDetails"]["videoId"] for it in items if "contentDetails" in it]
    stats = fetch_video_stats(ids)
    for it in items:
        vid = it["contentDetails"]["videoId"]
        snip = it["snippet"]
        st.session_state.videos.append({
            "videoId": vid,
            "title": snip.get("title"),
            "description": snip.get("description", ""),
            "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url"),
            "publishedAt": snip.get("publishedAt"),
            "stats": stats.get(vid, {}).get("statistics", {})
        })
    st.session_state.playlist_page_token = resp.get("nextPageToken")
    st.session_state.loading = False

# ------------------------------
# Fetch initial shorts or more shorts
# ------------------------------
def load_more_shorts():
    resp = fetch_search_short_videos(shorts_query, page_token=None if not st.session_state.shorts else st.session_state.shorts_token, max_results=12)
    items = resp.get("items", [])
    ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
    stats = fetch_video_stats(ids)
    for it in items:
        vid = it["id"]["videoId"]
        snip = it["snippet"]
        st.session_state.shorts.append({
            "videoId": vid,
            "title": snip.get("title"),
            "thumbnail": snip.get("thumbnails", {}).get("medium", {}).get("url"),
            "publishedAt": snip.get("publishedAt"),
            "stats": stats.get(vid, {}).get("statistics", {})
        })
    st.session_state.shorts_token = resp.get("nextPageToken")

# ------------------------------
# Auto infinite scroll trigger (JS -> clicks hidden button)
# ------------------------------
# hidden button that loads more
if "load_more_trigger" not in st.session_state:
    st.session_state.load_more_trigger = 0

# JS snippet: when user scrolls near bottom, click hidden 'streamlit load more' anchor
st.markdown(
    """
    <script>
    const threshold = 800; // pixels from bottom before triggering
    let ticking = false;
    window.addEventListener('scroll', function(e) {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(() => {
            const distanceToBottom = document.documentElement.scrollHeight - (window.innerHeight + window.scrollY);
            if (distanceToBottom < threshold) {
                const el = document.getElementById('streamlit-load-more');
                if (el) { el.click(); }
            }
            ticking = false;
        });
    });
    </script>
    """,
    unsafe_allow_html=True,
)

# The clickable invisible load-more element
if st.button("._load_more_", key="streamlit_hidden_loader"):
    # increment trigger
    st.session_state.load_more_trigger += 1
    # load more content
    if st.session_state.uploads_playlist_id:
        load_next_videos()
    if show_shorts:
        load_more_shorts()
    # re-run to update UI
    st.experimental_rerun()

# ------------------------------
# Initial auto-load if no videos yet and playlist present
# ------------------------------
if st.session_state.uploads_playlist_id and len(st.session_state.videos) == 0:
    load_next_videos()
    if show_shorts:
        load_more_shorts()

# ------------------------------
# UI: display videos in a responsive grid
# ------------------------------
st.markdown("## For You")
if not st.session_state.videos:
    st.info("No videos loaded yet. Enter a channel ID/username and press **Load channel**.")
else:
    # We'll render cards in 3 columns
    cols = st.columns(3)
    for idx, v in enumerate(st.session_state.videos):
        col = cols[idx % 3]
        with col:
            pub = v.get("publishedAt")
            pub_human = datetime.fromisoformat(pub.replace("Z", "+00:00")).strftime("%b %d, %Y") if pub else ""
            views = v.get("stats", {}).get("viewCount", "")
            views_text = f"{int(views):,} views" if views else ""
            col.markdown(f"""
                <div class="video-card">
                    <img class="video-thumb" src="{v['thumbnail']}" width="100%">
                    <div style="padding-top:8px;">
                      <div class="title">{v['title']}</div>
                      <div class="meta">{views_text} • {pub_human}</div>
                      <div class="desc">{v['description'][:160]}{'...' if len(v['description'])>160 else ''}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            # Play
            with col.expander("▶ Play"):
                st.video(f"https://www.youtube.com/watch?v={v['videoId']}")

# ------------------------------
# Shorts row
# ------------------------------
if show_shorts:
    st.markdown("---")
    st.markdown("### Life Story Shorts")
    if not st.session_state.shorts:
        st.info("No shorts loaded yet.")
    else:
        short_cols = st.columns(min(6, len(st.session_state.shorts)))
        for i, s in enumerate(st.session_state.shorts):
            sc = short_cols[i % len(short_cols)]
            with sc:
                st.markdown(f"""
                    <div class="video-card">
                        <img class="shorts-thumb" src="{s['thumbnail']}" width="100%">
                        <div style="padding-top:8px;">
                          <div class="title">{s['title']}</div>
                          <div class="meta">{s.get('stats', {}).get('viewCount', '')} views</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                with sc.expander("▶ Play"):
                    st.video(f"https://www.youtube.com/watch?v={s['videoId']}")

# ------------------------------
# Footer / status
# ------------------------------
st.markdown("---")
st.caption("This app uses the official YouTube Data API and embeds the official YouTube player. Replace the API key & channel input with your desired channel. Do not post your API key publicly.")
