# app.py
import streamlit as st
import requests
from datetime import datetime
import time

# ---------------------------
# Minimal dependencies: streamlit, requests
# ---------------------------
st.set_page_config(page_title="The Main One — For You", layout="wide")
st.markdown("""<style>
.stApp { background: #0f0f0f; color: #fff; }
.video-card { background:#151515; padding:10px; border-radius:10px; margin-bottom:12px; }
.thumb { border-radius:8px; }
.meta { color:#bdbdbd; font-size:13px; }
.title { color:#fff; font-weight:600; font-size:15px; margin-top:6px; }
.desc { color:#ccc; font-size:13px; margin-top:6px; }
</style>""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;'>🎬 The Main One — For You</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#bbb;margin-top:-12px;'>Public feed: Trending • Shorts • Channel videos</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------
# Config & inputs
# ---------------------------
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

# Prefer Streamlit Secrets; fallback to input
API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
if not API_KEY:
    API_KEY = st.text_input("Enter YouTube API Key (or set YOUTUBE_API_KEY in Streamlit Secrets)", type="password")

col1, col2 = st.columns([3,1])
with col1:
    channel_input = st.text_input("Optional channel (channel ID 'UC...' or name) to include", value="")
with col2:
    per_load = st.selectbox("Videos per load", [6,9,12,18], index=2)

include_shorts = st.checkbox("Include 'Life Story' Shorts", value=True)
shorts_query = st.text_input("Shorts search query", value="life story") if include_shorts else ""

region = st.selectbox("Trending region", ["US","GB","DE","IN","CA","AU"], index=0)
st.markdown("---")

# ---------------------------
# Helpers: YouTube API wrappers
# ---------------------------
def api_get(path, params):
    params = params.copy()
    params["key"] = API_KEY
    r = requests.get(f"{YOUTUBE_API_BASE}/{path}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def get_channel_id_from_username(username):
    username = username.strip()
    if username.startswith("UC"):
        return username
    # try forUsername
    try:
        data = api_get("channels", {"part":"id", "forUsername": username})
        if data.get("items"):
            return data["items"][0]["id"]
    except Exception:
        pass
    # fallback search
    data = api_get("search", {"part":"snippet", "q": username, "type":"channel", "maxResults":1})
    if data.get("items"):
        return data["items"][0]["snippet"]["channelId"]
    return None

def get_uploads_playlist_id(channel_id):
    data = api_get("channels", {"part":"contentDetails", "id": channel_id})
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

def fetch_playlist_items(playlist_id, page_token=None, max_results=12):
    params = {"part":"snippet,contentDetails", "playlistId":playlist_id, "maxResults": max_results}
    if page_token:
        params["pageToken"] = page_token
    return api_get("playlistItems", params)

def fetch_most_popular(region_code="US", max_results=12):
    return api_get("videos", {"part":"snippet,statistics,contentDetails", "chart":"mostPopular", "regionCode":region_code, "maxResults":max_results})

def search_shorts(query, page_token=None, max_results=12):
    params = {"part":"snippet", "q":query, "type":"video", "videoDuration":"short", "order":"date", "maxResults": max_results}
    if page_token:
        params["pageToken"] = page_token
    return api_get("search", params)

# ---------------------------
# Session state for feed & pagination
# ---------------------------
if "mixed_feed" not in st.session_state:
    st.session_state.mixed_feed = []
if "playlist_token" not in st.session_state:
    st.session_state.playlist_token = None
if "shorts_token" not in st.session_state:
    st.session_state.shorts_token = None
if "uploads_playlist_id" not in st.session_state:
    st.session_state.uploads_playlist_id = None
if "loaded_once" not in st.session_state:
    st.session_state.loaded_once = False
if "load_counter" not in st.session_state:
    st.session_state.load_counter = 0

# ---------------------------
# Load initial content (trending + channel + shorts)
# ---------------------------
def init_feed():
    st.session_state.mixed_feed = []
    # trending
    try:
        tp = fetch_most_popular(region_code=region, max_results=per_load)
        for it in tp.get("items", []):
            st.session_state.mixed_feed.append({
                "videoId": it["id"],
                "title": it["snippet"].get("title",""),
                "description": it["snippet"].get("description",""),
                "thumbnail": it["snippet"].get("thumbnails",{}).get("medium",{}).get("url"),
                "source":"trending",
                "publishedAt": it["snippet"].get("publishedAt","")
            })
    except Exception as e:
        st.warning("Could not load trending: " + str(e))

    # channel uploads if provided
    if channel_input:
        try:
            cid = get_channel_id_from_username(channel_input)
            if cid:
                pl = get_uploads_playlist_id(cid)
                if pl:
                    st.session_state.uploads_playlist_id = pl
                    resp = fetch_playlist_items(pl, max_results=per_load)
                    for it in resp.get("items", []):
                        vid = it["contentDetails"]["videoId"]
                        snip = it["snippet"]
                        st.session_state.mixed_feed.append({
                            "videoId": vid,
                            "title": snip.get("title",""),
                            "description": snip.get("description",""),
                            "thumbnail": snip.get("thumbnails",{}).get("medium",{}).get("url"),
                            "source":"channel",
                            "publishedAt": snip.get("publishedAt","")
                        })
                    st.session_state.playlist_token = resp.get("nextPageToken")
        except Exception as e:
            st.warning("Could not load channel: " + str(e))

    # shorts
    if include_shorts and shorts_query:
        try:
            sr = search_shorts(shorts_query, max_results=per_load)
            for it in sr.get("items", []):
                vid = it["id"].get("videoId")
                snip = it["snippet"]
                if vid:
                    st.session_state.mixed_feed.insert(0, {
                        "videoId": vid,
                        "title": snip.get("title",""),
                        "description": snip.get("description",""),
                        "thumbnail": snip.get("thumbnails",{}).get("medium",{}).get("url"),
                        "source":"shorts",
                        "publishedAt": snip.get("publishedAt","")
                    })
            st.session_state.shorts_token = sr.get("nextPageToken")
        except Exception as e:
            st.warning("Could not load shorts: " + str(e))

    # dedupe by videoId preserving order
    seen = set()
    dedup = []
    for it in st.session_state.mixed_feed:
        if it["videoId"] not in seen:
            dedup.append(it)
            seen.add(it["videoId"])
    st.session_state.mixed_feed = dedup
    st.session_state.loaded_once = True

# ---------------------------
# Load more content (called by hidden button)
# ---------------------------
def load_more():
    st.session_state.load_counter += 1
    # try to fetch more from uploads playlist
    if st.session_state.uploads_playlist_id and st.session_state.playlist_token is not None:
        try:
            resp = fetch_playlist_items(st.session_state.uploads_playlist_id, page_token=st.session_state.playlist_token, max_results=per_load)
            for it in resp.get("items", []):
                vid = it["contentDetails"]["videoId"]
                snip = it["snippet"]
                st.session_state.mixed_feed.append({
                    "videoId": vid,
                    "title": snip.get("title",""),
                    "description": snip.get("description",""),
                    "thumbnail": snip.get("thumbnails",{}).get("medium",{}).get("url"),
                    "source":"channel",
                    "publishedAt": snip.get("publishedAt","")
                })
            st.session_state.playlist_token = resp.get("nextPageToken")
        except Exception:
            pass

    # fetch more trending
    try:
        more = fetch_most_popular(region_code=region, max_results=per_load)
        for it in more.get("items", []):
            st.session_state.mixed_feed.append({
                "videoId": it["id"],
                "title": it["snippet"].get
