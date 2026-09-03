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
        # PDF links ko pehle hi skip karo
        if url.lower().endswith(".pdf") or "pdf" in url.lower():
            return None

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        # Content-Type check karo - sirf HTML process karo
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article")
        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text(strip=True) for p in paragraphs)

        # Cap - agar text bahut zyada bada hai, kuch galat hai, reject karo
        if text and len(text) > 50000:
            print(f"      → Skip (suspiciously large: {len(text)} chars, likely not real content)")
            return None

        return text if text and len(text) > 300 else None
    except Exception:
        return None

def collect_domain_knowledge(topic_name, search_queries):
    print(f"\n{'='*50}")
    print(f"Collecting domain knowledge for: {topic_name}")
    print(f"{'='*50}")

    all_urls_seen = set()
    collected_articles = []

    for query in search_queries:
        print(f"  Searching: {query}")
        results = search_duckduckgo(query, max_results=5)

        for r in results:
            if r["url"] in all_urls_seen:
                continue
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

    if len(collected_articles) == 0:
        print("  ⚠️  Koi article nahi mila - purani file safe rakhi ja rahi hai")
        return {"topic": topic_name, "total_articles": 0, "skipped_save": True}

    topic_data = {
        "topic": topic_name,
        "source": "web_articles",
        "total_articles": len(collected_articles),
        "articles": collected_articles
    }

    filename = f"../data/domain_knowledge/{topic_name.lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(topic_data, f, indent=2, ensure_ascii=False)

    print(f"  → Total collected: {len(collected_articles)} articles")
    print(f"Saved to {filename}")
    return topic_data

# ===== POLICY & INFRASTRUCTURE (CONCEPT-LEVEL) =====
policy_queries = [
    "FAME scheme India explained how it works",
    "EV road tax exemption India how it works state policy",
    "PLI scheme electric vehicle India explained",
    "India EV charging infrastructure types public home highway",
    "state EV policy India which states offer benefits"
]

result = collect_domain_knowledge("Policy and Infrastructure", policy_queries)