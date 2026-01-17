import streamlit as st
from pytube import YouTube
import re

# ---------- CONFIG ----------
st.set_page_config(page_title="🎬 YouTube Metadata Viewer", layout="centered")

# ---------- PAGE HEADER ----------
st.title("🎬 YouTube Metadata Viewer")
st.caption("Paste a YouTube URL to preview metadata — no downloads are performed.")

# ---------- HELPERS ----------
def normalize_youtube_url(url):
    """Convert any YouTube URL to standard format for pytube."""
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return None

# ---------- USER INPUT ----------
query = st.text_input("🔍 Paste YouTube URL", placeholder="https://www.youtube.com/watch?v=xxxxx")
search_clicked = st.button("Get Metadata", type="primary", use_container_width=True)

# ---------- PROCESS ----------
if search_clicked:
    if not query.strip():
        st.error("Please enter a YouTube URL.")
    else:
        query = normalize_youtube_url(query)
        if not query:
            st.error("Invalid YouTube URL. Make sure it’s a full video link.")
            st.stop()
        try:
            yt = YouTube(query)

            st.success("Metadata extracted successfully!")

            # Display thumbnail
            st.image(yt.thumbnail_url, caption="Thumbnail")

            # Metadata dictionary
            metadata = {
                "title": yt.title,
                "channel": yt.author,
                "views": yt.views,
                "length_seconds": yt.length,
                "publish_date": str(yt.publish_date),
                "url": query,
                "description": yt.description[:300] + "..." if yt.description else ""
            }

            # Display metadata as JSON
            st.subheader("Video Metadata (JSON)")
            st.json(metadata)

            # Embed video
            st.subheader("Embedded Video")
            st.video(query)

        except Exception as e:
            st.error(f"❌ Error processing this URL: {e}")
