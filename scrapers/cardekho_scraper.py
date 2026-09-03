import requests
from bs4 import BeautifulSoup
import re
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

# Terminology fix - EV ke liye "mileage" ko "range" karenge
ASPECT_RENAME = {
    "mileage": "range"
}

def clean_author_date(raw_text):
    parts = raw_text.split("|")
    author = parts[0].strip() if len(parts) > 0 else "Unknown"
    date = parts[-1].strip() if len(parts) > 0 else "Unknown"
    return author, date

def fetch_car_metadata(slug):
    url = f"https://www.cardekho.com/{slug}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    aspect_tags = {}
    nav_items = soup.select("ul.galleryNav.ReviewsTab > li")
    for item in nav_items:
        title = item.get("title", "")
        if title and title != "More":
            text = item.get_text(strip=True)
            match = re.search(r'\((\d+)\)', text)
            count = int(match.group(1)) if match else 0
            key = title.lower()
            key = ASPECT_RENAME.get(key, key)  # rename agar zaroori ho
            aspect_tags[key] = count

    overall_rating = None
    total_reviews = None
    based_on_span = soup.find(string=lambda t: t and "Based on" in t)
    if based_on_span:
        parent = based_on_span.find_parent("div")
        if parent:
            full_text = parent.get_text(separator="|", strip=True)
            rating_match = re.search(r'([\d.]+)\|/5', full_text)
            reviews_match = re.search(r'(\d+)\s*User Reviews', full_text)
            overall_rating = float(rating_match.group(1)) if rating_match else None
            total_reviews = int(reviews_match.group(1)) if reviews_match else None

    return {
        "overall_rating": overall_rating,
        "total_reviews": total_reviews,
        "aspect_tags": aspect_tags
    }

def fetch_reviews_page(slug, page_number):
    if page_number == 1:
        url = f"https://www.cardekho.com/{slug}/user-reviews"
    else:
        url = f"https://www.cardekho.com/{slug}/user-reviews/{page_number}"

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    review_items = soup.select("ul.reviewList > li")

    if len(review_items) == 0:
        return []

    page_reviews = []
    for item in review_items:
        try:
            name_div = item.select_one("div.name")
            raw_text = name_div.get_text(strip=True, separator="|") if name_div else ""
            author, date = clean_author_date(raw_text)

            rating_span = item.select_one("span.ratingStarNew")
            rating = rating_span.get_text(strip=True) if rating_span else None

            title_span = item.select_one("span.title")
            title = title_span.get_text(strip=True) if title_span else ""

            content_div = item.select_one("div.contentheight div")
            review_text = content_div.get_text(strip=True) if content_div else ""

            page_reviews.append({
                "author": author,
                "date": date,
                "rating": rating,
                "title": title,
                "text": review_text
            })
        except Exception as e:
            print("Error parsing one review:", e)

    return page_reviews

def fetch_all_reviews(slug, max_pages=25):
    all_reviews = []
    seen_review_keys = set()
    page = 1
    consecutive_duplicate_pages = 0

    while page <= max_pages:
        page_reviews = fetch_reviews_page(slug, page)

        if len(page_reviews) == 0:
            print(f"    Page {page} khaali - stopping.")
            break

        new_reviews_this_page = 0
        for r in page_reviews:
            key = (r["author"], r["title"], r["date"])
            if key not in seen_review_keys:
                seen_review_keys.add(key)
                all_reviews.append(r)
                new_reviews_this_page += 1

        print(f"    Page {page}: {new_reviews_this_page} new reviews mile (out of {len(page_reviews)} total)")

        if new_reviews_this_page == 0:
            consecutive_duplicate_pages += 1
            print(f"    Consecutive duplicate pages: {consecutive_duplicate_pages}")
            if consecutive_duplicate_pages >= 2:
                print(f"    2 baar duplicate mila - genuinely end aa gaya, stopping.")
                break
        else:
            consecutive_duplicate_pages = 0  # reset, kyunki naya data mila

        page += 1
        time.sleep(2)

    return all_reviews

def collect_car_data(car_name, slug):
    print(f"\n{'='*50}")
    print(f"Collecting data for: {car_name} ({slug})")
    print(f"{'='*50}")

    print("Fetching metadata (aspect tags, rating)...")
    metadata = fetch_car_metadata(slug)
    print(f"  → Rating: {metadata['overall_rating']}, Total Reviews: {metadata['total_reviews']}")

    print("Fetching reviews (all pages)...")
    reviews = fetch_all_reviews(slug, max_pages=20)
    print(f"  → Collected {len(reviews)} reviews")

    car_data = {
        "car_name": car_name,
        "slug": slug,
        "source": "cardekho",
        "metadata": metadata,
        "reviews": reviews
    }

    # Filename banate hain slug se (safe filename ke liye / ko _ karenge)
    filename = f"../data/cardekho/{slug.replace('/', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {filename}")
    return car_data

# ===== 5 CARS KI LIST =====
cars_to_collect = [
    ("Mahindra BE 6", "mahindra/be-6"),
    ("Mahindra XEV 9e", "mahindra/xev-9e"),
    ("Mahindra XEV 9s", "mahindra/xev-9s"),
    ("Tata Harrier EV", "tata/harrier-ev"),
    ("Tata Sierra EV", "tata/sierra-ev"),
]

all_results = []
result = collect_car_data("Mahindra BE 6", "mahindra/be-6")
for car_name, slug in cars_to_collect:
    result = collect_car_data(car_name, slug)
    all_results.append(result)
    time.sleep(3)  # Cars ke beech extra gap - respectful scraping

print(f"\n\n{'='*50}")
print(f"DONE! Total cars collected: {len(all_results)}")
for r in all_results:
    print(f"  - {r['car_name']}: {len(r['reviews'])} reviews")