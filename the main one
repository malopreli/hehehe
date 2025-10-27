import streamlit as st
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import itertools

st.set_page_config(page_title="YouTube For You", layout="wide")
st.title("YouTube For You – Streamlit Edition")

# -----------------------------
# Google OAuth 2.0 Setup
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# Run the OAuth flow (desktop app flow)
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
credentials = flow.run_local_server(port=0)
youtube = build("youtube", "v3", credentials=credentials)

st.success("Signed in successfully!")

# -----------------------------
# Fetch subscriptions
# -----------------------------
subs_request = youtube.subscriptions().list(
    part="snippet",
    mine=True,
    maxResults=5
)
subs_response = subs_request.execute()

videos = []

for sub in subs_response.get('items', []):
    channel_id = sub['snippet']['resourceId']['channelId']
    search_request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=2,
        type="video"
    )
    search_response = search_request.execute()
    videos.extend(search_response.get('items', []))

# -----------------------------
# Fetch liked videos
# -----------------------------
try:
    liked_request = youtube.videos().list(
        part="snippet,statistics",
        myRating="like",
        maxResults=5
    )
    liked_response = liked_request.execute()
    videos.extend(liked_response.get('items', []))
except Exception as e:
    st.info("Could not fetch liked videos. Make sure your account has liked videos and OAuth scopes are correct.")

# -----------------------------
# Fetch Shorts (popular short-form videos)
# -----------------------------
shorts_request = youtube.search().list(
    part="snippet",
    maxResults=10,
    type="video",
    videoDuration="short",
    order="viewCount"
)
shorts_response = shorts_request.execute()
videos.extend(shorts_response.get('items', []))

# -----------------------------
# Display videos in a grid (3 columns)
# -----------------------------
st.subheader("Your For You Feed")
columns = st.columns(3)

for idx, video in enumerate(videos):
    col = columns[idx % 3]
    snippet = video['snippet']
    title = snippet['title']
    video_id = video['id'].get('videoId') or video.get('id')  # handle liked videos
    thumbnail = snippet['thumbnails']['medium']['url']

    col.image(thumbnail)
    col.write(title)
    col.video(f"https://www.youtube.com/watch?v={video_id}")

# -----------------------------
# Optional: Infinite scroll
# -----------------------------
st.info("Scroll to see more videos! Adjust maxResults in the code for more content.")
