import streamlit as st
import random

# ---------- Page Config ----------
st.set_page_config(page_title="The Main One", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
    <style>
    body {
        background-color: #0f0f0f;
        color: #f1f1f1;
        font-family: 'Segoe UI', sans-serif;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .video-card {
        background-color: #1c1c1c;
        border-radius: 12px;
        padding: 10px;
        transition: all 0.2s ease-in-out;
    }
    .video-card:hover {
        transform: scale(1.02);
        background-color: #2a2a2a;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
    }
    .video-thumb {
        border-radius: 10px;
    }
    .shorts-card {
        background-color: #1c1c1c;
        border-radius: 16px;
        padding: 8px;
        text-align: center;
        transition: all 0.2s ease-in-out;
    }
    .shorts-card:hover {
        transform: scale(1.05);
        background-color: #272727;
    }
    </style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("<h1 style='text-align:center;'>📺 The Main One</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#ccc;'>Your Personalized Video Feed</h4>", unsafe_allow_html=True)
st.markdown("---")

# ---------- Mock Data (replace with API later) ----------
VIDEOS = [
    {
        "title": "Relaxing Ocean Waves 🌊",
        "channel": "NatureHub",
        "description": "Listen to calming ocean waves for deep relaxation.",
        "thumbnail": "https://i.ytimg.com/vi/9bZkp7q19f0/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=9bZkp7q19f0"
    },
    {
        "title": "Epic Space Journey 🚀",
        "channel": "CosmosX",
        "description": "A visual adventure through galaxies and nebulae.",
        "thumbnail": "https://i.ytimg.com/vi/DLX62G4lc44/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=DLX62G4lc44"
    },
    {
        "title": "How to Cook Perfect Pasta 🍝",
        "channel": "ChefZone",
        "description": "Learn the secret to making perfect pasta every time.",
        "thumbnail": "https://i.ytimg.com/vi/eBGIQ7ZuuiU/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=eBGIQ7ZuuiU"
    },
    {
        "title": "Cinematic Drone Shots 🛸",
        "channel": "SkyVision",
        "description": "Aerial footage that feels out of this world.",
        "thumbnail": "https://i.ytimg.com/vi/rYEDA3JcQqw/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=rYEDA3JcQqw"
    },
]

SHORTS = [
    {
        "title": "Mini Pizza in 30s 🍕",
        "thumbnail": "https://i.ytimg.com/vi/6Dh-RL__uN4/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=6Dh-RL__uN4"
    },
    {
        "title": "Tiny Planet Time-lapse 🌍",
        "thumbnail": "https://i.ytimg.com/vi/tAGnKpE4NCI/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=tAGnKpE4NCI"
    },
    {
        "title": "Cat jumps higher than expected 😹",
        "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    }
]

# ---------- Infinite Scroll Setup ----------
if "page" not in st.session_state:
    st.session_state.page = 1

VIDEOS_PER_PAGE = 3

def get_videos(page):
    data = random.sample(VIDEOS * 5, len(VIDEOS) * 5)
    start = (page - 1) * VIDEOS_PER_PAGE
    end = start + VIDEOS_PER_PAGE
    return data[start:end]

# ---------- Main Feed ----------
st.subheader("For You")
cols = st.columns(3)

for i, video in enumerate(get_videos(st.session_state.page)):
    with cols[i % 3]:
        st.markdown(f"""
            <div class="video-card">
                <img class="video-thumb" src="{video['thumbnail']}" width="100%" />
                <h4>{video['title']}</h4>
                <p style="color:#bbb;">{video['channel']}</p>
                <p style="font-size:13px; color:#999;">{video['description']}</p>
            </div>
        """, unsafe_allow_html=True)
        with st.expander("▶ Play video"):
            st.video(video["url"])

# ---------- Shorts ----------
st.subheader("Shorts 🎥")
short_cols = st.columns(len(SHORTS))
for i, short in enumerate(SHORTS):
    with short_cols[i]:
        st.markdown(f"""
            <div class="shorts-card">
                <img src="{short['thumbnail']}" width="100%" />
                <p>{short['title']}</p>
            </div>
        """, unsafe_allow_html=True)
        st.video(short["url"])

# ---------- Load More ----------
if st.button("Load More"):
    st.session_state.page += 1
    st.rerun()
