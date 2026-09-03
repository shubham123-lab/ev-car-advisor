import requests
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_videos(query, max_results=8):
    """YouTube Data API se video search karta hai"""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
        "relevanceLanguage": "en"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if "error" in data:
        print("API Error:", data["error"])
        return []

    videos = []
    for item in data.get("items", []):
        videos.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "published": item["snippet"]["publishedAt"]
        })
    return videos

def fetch_transcript(video_id):
    """Ek video ka transcript nikalta hai (agar available ho)"""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=["en", "hi"])
        transcript_list = transcript.to_raw_data()
        full_text = " ".join(chunk['text'] for chunk in transcript_list)
        return full_text
    except TranscriptsDisabled:
        return None
    except Exception as e:
        print(f"    Transcript error for {video_id}: {type(e).__name__}")
        return None

def collect_youtube_data(car_name, search_query):
    print(f"\n{'='*50}")
    print(f"Collecting YouTube data for: {car_name}")
    print(f"{'='*50}")

    print("Searching videos...")
    videos = search_videos(search_query, max_results=8)
    print(f"  → {len(videos)} videos mile")

    collected = []
    for v in videos:
        print(f"  Fetching transcript: {v['title'][:50]}...")
        transcript = fetch_transcript(v["video_id"])

        if transcript and len(transcript) > 200:
            collected.append({
                "video_id": v["video_id"],
                "title": v["title"],
                "channel": v["channel"],
                "published": v["published"],
                "transcript": transcript
            })
            print(f"    → Transcript mila ({len(transcript)} chars)")
        else:
            print(f"    → Transcript nahi mila, skip")

        time.sleep(5)  # rate limiting - IP ban se bachne ke liye badhaya

    filename = f"../data/youtube/{car_name.lower().replace(' ', '_')}.json"

    # SAFETY CHECK - khaali data pe purani achhi file overwrite mat karo
    if len(collected) == 0:
        print(f"  ⚠️  Koi transcript nahi mila is run me — purani file (agar hai) SAFE rakhi ja rahi hai.")
        return {"car_name": car_name, "total_videos_collected": 0, "skipped_save": True}

    car_data = {
        "car_name": car_name,
        "source": "youtube",
        "total_videos_collected": len(collected),
        "videos": collected
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {filename}")
    return car_data

# ===== 5 CARS KI LIST =====
cars_to_collect = [
    ("Mahindra BE 6", "Mahindra BE 6 review"),
    ("Mahindra XEV 9e", "Mahindra XEV 9e review"),
    ("Mahindra XEV 9s", "Mahindra XEV 9s review"),
    ("Tata Harrier EV", "Tata Harrier EV review"),
    ("Tata Sierra EV", "Tata Sierra EV review"),
]

all_results = []
for car_name, search_query in cars_to_collect:
    result = collect_youtube_data(car_name, search_query)
    all_results.append(result)
    time.sleep(10)  # cars ke beech extra gap - safety ke liye badhaya

print(f"\n\n{'='*50}")
print("DONE! Summary:")
for r in all_results:
    status = f"{r['total_videos_collected']} videos" if not r.get("skipped_save") else "SKIPPED (no data, old file preserved)"
    print(f"  - {r['car_name']}: {status}")