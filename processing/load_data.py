import json
import glob
from langchain_core.documents import Document
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_cardekho_data():
    """CarDekho reviews load karta hai"""
    documents = []
    files = glob.glob(os.path.join(DATA_DIR, "cardekho", "*.json"))

    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            car_data = json.load(f)
        
        car_name = car_data["car_name"]
        
        for review in car_data["reviews"]:
            if len(review["text"]) < 50:
                continue
            
            doc = Document(
                page_content=review["text"],
                metadata={
                    "car_name": car_name,
                    "source": "cardekho",
                    "author": review["author"],
                    "date": review["date"],
                    "rating": review["rating"],
                    "title": review["title"]
                }
            )
            documents.append(doc)
    
    print(f"  CarDekho: {len(documents)} documents")
    return documents


def load_carwale_data():
    """CarWale reviews load karta hai"""
    documents = []
    files = glob.glob(os.path.join(DATA_DIR, "carwale", "*.json"))
    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            car_data = json.load(f)
        
        car_name = car_data["car_name"]
        
        for review in car_data["reviews"]:
            # CarWale me title + text dono combine karte hain, kyunki text kabhi chhota hota hai
            combined_text = f"{review['title']}. {review['text']}"
            if len(combined_text) < 50:
                continue
            
            doc = Document(
                page_content=combined_text,
                metadata={
                    "car_name": car_name,
                    "source": "carwale",
                    "rating": review.get("rating"),
                }
            )
            documents.append(doc)
    
    print(f"  CarWale: {len(documents)} documents")
    return documents


def load_web_articles_data():
    """Web articles (car-specific) load karta hai"""
    documents = []
    files = glob.glob(os.path.join(DATA_DIR, "web_articles", "*.json"))

    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            car_data = json.load(f)
        
        car_name = car_data["car_name"]
        
        for article in car_data["articles"]:
            # Ad-tracking URLs skip karo (genuine article nahi hai)
            url = article.get("url", "")
            if "duckduckgo.com/y.js" in url or "bing.com/aclick" in url:
                continue
            
            if len(article["text"]) < 100:
                continue
            
            doc = Document(
                page_content=article["text"],
                metadata={
                    "car_name": car_name,
                    "source": "web_article",
                    "title": article["title"],
                    "url": article["url"]
                }
            )
            documents.append(doc)
    
    print(f"  Web Articles: {len(documents)} documents")
    return documents


def load_youtube_data():
    """YouTube transcripts load karta hai (jo mila hai)"""
    documents = []
    files = glob.glob(os.path.join(DATA_DIR, "youtube", "*.json"))
    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            car_data = json.load(f)
        
        car_name = car_data["car_name"]
        
        for video in car_data.get("videos", []):
            if len(video["transcript"]) < 100:
                continue
            
            doc = Document(
                page_content=video["transcript"],
                metadata={
                    "car_name": car_name,
                    "source": "youtube",
                    "title": video["title"],
                    "channel": video["channel"],
                    "video_id": video["video_id"]
                }
            )
            documents.append(doc)
    
    print(f"  YouTube: {len(documents)} documents")
    return documents


def load_domain_knowledge_data():
    """Policy aur Technology - car-specific NAHI hai, isliye car_name nahi hoga"""
    documents = []
    files = glob.glob(os.path.join(DATA_DIR, "domain_knowledge", "*.json"))
    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            topic_data = json.load(f)
        
        topic = topic_data["topic"]
        
        for article in topic_data["articles"]:
            if len(article["text"]) < 100:
                continue
            
            doc = Document(
                page_content=article["text"],
                metadata={
                    "topic": topic,
                    "source": "domain_knowledge",
                    "title": article["title"],
                    "url": article["url"]
                }
            )
            documents.append(doc)
    
    print(f"  Domain Knowledge: {len(documents)} documents")
    return documents


def load_all_documents():
    """Sabko combine karta hai"""
    print("Loading all sources...")
    all_docs = []
    all_docs.extend(load_cardekho_data())
    all_docs.extend(load_carwale_data())
    all_docs.extend(load_web_articles_data())
    all_docs.extend(load_youtube_data())
    all_docs.extend(load_domain_knowledge_data())
    
    print(f"\nTOTAL DOCUMENTS: {len(all_docs)}")
    return all_docs


# Test
if __name__ == "__main__":
    docs = load_all_documents()
    
    print("\n--- Sample from each source ---")
    seen_sources = set()
    for doc in docs:
        src = doc.metadata.get("source")
        if src not in seen_sources:
            seen_sources.add(src)
            print(f"\n[{src}]")
            print("Content:", doc.page_content[:150])
            print("Metadata:", doc.metadata)