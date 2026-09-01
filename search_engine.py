import requests
import re
from urllib.parse import quote_plus, unquote
from wikipedia import search_wikipedia_passages, clean_question_query

def search_duckduckgo_api(query: str) -> list[dict]:
    """Fetch instant answers and abstract text from DuckDuckGo API."""
    try:
        clean_q = clean_question_query(query)
        target = clean_q if clean_q else query
        url = f"https://api.duckduckgo.com/?q={quote_plus(target)}&format=json&no_html=1&skip_disambig=1"
        res = requests.get(url, headers={"User-Agent": "HallucinationAgent/3.0"}, timeout=4)
        if res.status_code == 200:
            data = res.json()
            passages = []
            abstract = data.get("AbstractText", "").strip()
            heading = data.get("Heading", "").strip()
            source_url = data.get("AbstractURL", f"https://duckduckgo.com/?q={quote_plus(target)}")
            
            if abstract:
                passages.append({
                    "engine": "DuckDuckGo Instant Answer",
                    "title": heading if heading else f"DuckDuckGo Answer: {target}",
                    "snippet": abstract,
                    "url": source_url if source_url else f"https://duckduckgo.com/?q={quote_plus(target)}"
                })
                
            related = data.get("RelatedTopics", [])
            for rel in related:
                if isinstance(rel, dict) and "Text" in rel and len(rel["Text"]) > 20:
                    passages.append({
                        "engine": "DuckDuckGo Related",
                        "title": rel.get("FirstURL", "").split("/")[-1].replace("_", " ") or "Web Reference",
                        "snippet": rel["Text"],
                        "url": rel.get("FirstURL", f"https://duckduckgo.com/?q={quote_plus(target)}")
                    })
                    if len(passages) >= 3:
                        break
            return passages
    except Exception:
        pass
    return []

def search_duckduckgo_passages(query: str, max_results: int = 4) -> list[dict]:
    """
    Fallback web search using DuckDuckGo Instant Answer API & HTML Search.
    """
    passages = search_duckduckgo_api(query)
    if len(passages) >= max_results:
        return passages[:max_results]

    try:
        clean_q = clean_question_query(query)
        target = clean_q if clean_q else query
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(target)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', res.text, re.DOTALL)
            titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', res.text, re.DOTALL)
            
            for i in range(min(len(snippets), max_results - len(passages))):
                clean_snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                clean_title = re.sub(r'<[^>]+>', '', titles[i]).strip() if i < len(titles) else "Web Evidence"
                if clean_snippet:
                    passages.append({
                        "engine": "DuckDuckGo Web",
                        "title": clean_title if clean_title else "Web Article",
                        "snippet": clean_snippet,
                        "url": f"https://duckduckgo.com/?q={quote_plus(target)}"
                    })
    except Exception:
        pass

    return passages[:max_results]

def get_hybrid_evidence(query: str, max_results: int = 4, engine: str = "hybrid") -> list[dict]:
    """
    Retrieve evidence using Wikipedia REST API and web search fallback if needed.
    """
    evidence = []
    clean_q = clean_question_query(query)
    
    if engine in ["wikipedia", "hybrid"]:
        wiki_passages = search_wikipedia_passages(query, max_results=max_results)
        if wiki_passages:
            evidence.extend(wiki_passages)
        elif clean_q and clean_q != query:
            wiki_passages = search_wikipedia_passages(clean_q, max_results=max_results)
            if wiki_passages:
                evidence.extend(wiki_passages)
            
    if engine in ["web", "hybrid"] and len(evidence) < max_results:
        ddg_passages = search_duckduckgo_passages(query, max_results=max_results - len(evidence))
        if ddg_passages:
            evidence.extend(ddg_passages)
            
    return evidence[:max_results]
