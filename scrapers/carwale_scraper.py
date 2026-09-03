import requests
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_reviews_page(carname, makename, page_number):
    url = (f"https://www.carwale.com/api/userreviews/listingpage/"
           f"?m=1&isApiCall=true&page={page_number}&carname={carname}"
           f"&versionId=0&ratingCriteria=0&sortingCriteria=1&makename={makename}")

    response = requests.get(url, headers=headers)
    try:
        data = response.json()
    except Exception:
        return [], None

    reviews = data.get("userReviewList", {}).get("Reviews", [])
    return reviews, data

def fetch_all_reviews(carname, makename, max_pages=30):
    all_reviews = []
    page = 1
    metadata = None

    while page <= max_pages:
        reviews, data = fetch_reviews_page(carname, makename, page)

        if page == 1:
            metadata = data  # pehle page se overall metadata bhi save karte hain

        if len(reviews) == 0:
            print(f"    Page {page} khaali - stopping.")
            break

        all_reviews.extend(reviews)
        print(f"    Page {page}: {len(reviews)} reviews mile")

        if len(reviews) < 10:
            print(f"    Page {page} incomplete (last page) - stopping.")
            break

        page += 1
        time.sleep(1.5)

    return all_reviews, metadata

def extract_clean_review(raw_review):
    """Sirf zaroori fields nikalte hain, poora bhara-bharaya object nahi"""
    return {
        "title": raw_review.get("Title", ""),
        "text": raw_review.get("Description", ""),
        "tips": raw_review.get("TipsAdvices", ""),
        "rating": raw_review.get("RatingInfo", {}).get("UserRating", None)
    }

def collect_car_data(car_name, carname_slug, makename):
    print(f"\n{'='*50}")
    print(f"Collecting data for: {car_name} ({carname_slug})")
    print(f"{'='*50}")

    raw_reviews, metadata = fetch_all_reviews(carname_slug, makename)
    clean_reviews = [extract_clean_review(r) for r in raw_reviews]

    car_data = {
        "car_name": car_name,
        "slug": carname_slug,
        "source": "carwale",
        "total_reviews_collected": len(clean_reviews),
        "reviews": clean_reviews
    }

    filename = f"../data/carwale/{carname_slug}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"  → Total collected: {len(clean_reviews)} reviews")
    print(f"Saved to {filename}")
    return car_data

# ===== 4 CARS (BE6 skip - CarDekho se already covered) =====
cars_to_collect = [
    ("Mahindra XEV 9e", "xev-9e", "mahindra"),
    ("Mahindra XEV 9s", "xev-9s", "mahindra"),
    ("Tata Harrier EV", "harrier-ev", "tata"),
    ("Tata Sierra EV", "sierra-ev", "tata"),
]

all_results = []
for car_name, slug, make in cars_to_collect:
    result = collect_car_data(car_name, slug, make)
    all_results.append(result)
    time.sleep(2)

print(f"\n\n{'='*50}")
print("DONE! Summary:")
for r in all_results:
    print(f"  - {r['car_name']}: {r['total_reviews_collected']} reviews")