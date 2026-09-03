import requests
from bs4 import BeautifulSoup
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def search_duckduckgo(query, max_results=5):
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    try:
        response = requests.post(url, data=params, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for link in soup.select("a.result__a")[:max_results]:
            title = link.get_text(strip=True)
            href = link.get("href")
            results.append({"title": title, "url": href})
        return results
    except Exception as e:
        print("Search error:", e)
        return []

def fetch_article_text(url):
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return None  # blocked ya error - chup-chaap skip karo

        soup = BeautifulSoup(response.text, "html.parser")

        article = soup.find("article")
        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(strip=True) for p in paragraphs)

        return text if len(text) > 300 else None  # bahut chhota text bhi skip karo
    except Exception:
        return None

def collect_web_articles(car_name, search_queries):
    print(f"\n{'='*50}")
    print(f"Collecting web articles for: {car_name}")
    print(f"{'='*50}")

    all_urls_seen = set()
    collected_articles = []

    for query in search_queries:
        print(f"  Searching: {query}")
        results = search_duckduckgo(query, max_results=5)

        for r in results:
            if r["url"] in all_urls_seen:
                continue  # duplicate URL skip karo
            all_urls_seen.add(r["url"])

            print(f"    Fetching: {r['title'][:60]}...")
            text = fetch_article_text(r["url"])

            if text:
                collected_articles.append({
                    "title": r["title"],
                    "url": r["url"],
                    "text": text
                })
                print(f"      → Mila ({len(text)} chars)")
            else:
                print(f"      → Skip (blocked/empty)")

            time.sleep(2)

    # Safety check - khaali data pe overwrite mat karo
    if len(collected_articles) == 0:
        print("  ⚠️  Koi article nahi mila - purani file safe rakhi ja rahi hai")
        return {"car_name": car_name, "total_articles": 0, "skipped_save": True}

    car_data = {
        "car_name": car_name,
        "source": "web_articles",
        "total_articles": len(collected_articles),
        "articles": collected_articles
    }

    filename = f"../data/web_articles/{car_name.lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"  → Total collected: {len(collected_articles)} articles")
    print(f"Saved to {filename}")
    return car_data

# ===== TEST - PEHLE SIRF BE6 =====
# ===== 5 CARS KI LIST — HAR EK KE LIYE 3 QUERIES =====
cars_config = [
    ("Mahindra BE 6", [
        "Mahindra BE 6 real world range review",
        "Mahindra BE 6 charging cost India",
        "Mahindra BE 6 common problems owner review"
    ]),
    ("Mahindra XEV 9e", [
        "Mahindra XEV 9e real world range review",
        "Mahindra XEV 9e charging cost India",
        "Mahindra XEV 9e common problems owner review"
    ]),
    ("Mahindra XEV 9s", [
        "Mahindra XEV 9s real world range review",
        "Mahindra XEV 9s charging cost India",
        "Mahindra XEV 9s common problems owner review"
    ]),
    ("Tata Harrier EV", [
        "Tata Harrier EV real world range review",
        "Tata Harrier EV charging cost India",
        "Tata Harrier EV common problems owner review"
    ]),
    ("Tata Sierra EV", [
        "Tata Sierra EV real world range review",
        "Tata Sierra EV charging cost India",
        "Tata Sierra EV common problems owner review"
    ]),
]

all_results = []
for car_name, queries in cars_config:
    result = collect_web_articles(car_name, queries)
    all_results.append(result)
    time.sleep(3)  # cars ke beech extra gap

print(f"\n\n{'='*50}")
print("DONE! Summary:")
for r in all_results:
    print(f"  - {r['car_name']}: {r.get('total_articles', 0)} articles")