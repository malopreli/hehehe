import streamlit as st
import requests

# ✅ Load your API key from Streamlit secrets
API_KEY = st.secrets["YOUTUBE_API_KEY"]

st.set_page_config(page_title="The Main One", page_icon="🎬", layout="wide")

st.title("🎬 The Main One")
st.write("Search YouTube videos directly — without going to YouTube.com")

# --- Search bar ---
query = st.text_input("🔍 Search for videos:", placeholder="Type something like 'Callus Box shorts'...")

# --- Search results ---
if query:
    st.write(f"### Results for **{query}**")
    
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 12,
        "key": API_KEY,
    }

    response = requests.get(search_url, params=params)
    data = response.json()

    if "items" in data:
        cols = st.columns(3)
        for i, item in enumerate(data["items"]):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            channel = item["snippet"]["channelTitle"]
            thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            with cols[i % 3]:
                st.image(thumbnail, use_container_width=True)
                st.markdown(f"[**{title}**]({url})")
                st.caption(f"by {channel}")
    else:
        st.error("No videos found or API limit reached 😔")

else:
    st.info("🔎 Type something above to search YouTube videos.")
