import re
import html
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor

def clean_text(text: str) -> str:
    """Clean whitespace, HTML formatting, IPA phonetics, and unescape HTML entities."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = html.unescape(clean)
    # Remove IPA phonetic pronunciation blocks like (/.../) or [...\u0281...]
    clean = re.sub(r'\([/\\][^)]+\)', '', clean)
    clean = re.sub(r'\[[/\\][^\]]+\]', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean.strip()

def clean_question_query(query: str) -> str:
    """Strip question filler words (where is, what is, located, etc.) to extract core target entity."""
    if not query:
        return ""
    q = query.strip()
    q = re.sub(r'^(where|what|who|when|why|how)\s+(is|are|was|were|located|can|did|do|does|the|a|an)\s+', '', q, flags=re.IGNORECASE).strip()
    q = re.sub(r'\b(located|situated|find|found|place|based|headquartered)\b.*$', '', q, flags=re.IGNORECASE).strip()
    q = re.sub(r'[?\!\.]', '', q).strip()
    return q if len(q) >= 2 else query.replace("?", "").strip()

def get_wikipedia_extract(title: str, headers: dict) -> str:
    """Fetch lead article summary of a Wikipedia article."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "titles": title,
        "format": "json",
        "redirects": 1
    }
    try:
        res = requests.get(url, params=params, headers=headers, timeout=5)
        if res.status_code == 200:
            pages = res.json().get("query", {}).get("pages", {})
            for pid, pdata in pages.items():
                extract = pdata.get("extract", "")
                if extract:
                    return clean_text(extract[:1000])
    except Exception:
        pass
    return ""

def extract_main_entities(query: str) -> list[str]:
    """Extract primary target entity names from query."""
    clean_target = clean_question_query(query)
    entities = []
    if clean_target and clean_target.lower() != query.lower():
        entities.append(clean_target)
        
    words = query.split()
    capitalized = [w for w in words if w and w[0].isupper() and len(w) > 1 and w.lower() not in ["the", "a", "an", "is", "was", "in", "of", "and", "or", "for", "to", "by", "where", "what", "who", "when"]]
    if len(capitalized) >= 2:
        cap_phrase = " ".join(capitalized[:3])
        if cap_phrase not in entities:
            entities.append(cap_phrase)
    for cap in capitalized:
        if len(cap) > 2 and cap not in entities:
            entities.append(cap)
            
    return entities

def search_wikipedia_engine(query: str) -> list[dict]:
    """Retrieve evidence passages from Wikipedia search and extracts."""
    url = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "AIHallucinationDetector/3.0"}
    
    titles_to_fetch = []
    
    core_target = clean_question_query(query)
    if core_target:
        titles_to_fetch.append(core_target)
        
    main_entities = extract_main_entities(query)
    for entity in main_entities:
        if entity not in titles_to_fetch:
            titles_to_fetch.append(entity)
        
    search_queries = [core_target, query] if core_target != query else [query]
    search_snippets = {}
    
    for sq in search_queries:
        if not sq:
            continue
        params = {"action": "query", "list": "search", "srsearch": sq, "format": "json", "utf8": 1}
        try:
            res = requests.get(url, params=params, headers=headers, timeout=5)
            if res.status_code == 200:
                results = res.json().get("query", {}).get("search", [])
                for r in results[:4]:
                    t = r.get("title", "")
                    snip = clean_text(r.get("snippet", ""))
                    if t:
                        if t not in titles_to_fetch:
                            titles_to_fetch.append(t)
                        if snip:
                            search_snippets[t] = snip
        except Exception:
            pass
        
    evidence_items = []
    seen_titles = set()
    for title in titles_to_fetch[:5]:
        if title in seen_titles:
            continue
        seen_titles.add(title)
        
        extract = get_wikipedia_extract(title, headers)
        search_snip = search_snippets.get(title, "")
        
        combined_text = extract
        if search_snip and search_snip.lower() not in extract.lower():
            combined_text = f"{extract} ... {search_snip}" if extract else search_snip
            
        if combined_text:
            encoded_title = urllib.parse.quote(title.replace(" ", "_"))
            evidence_items.append({
                "engine": "Wikipedia",
                "title": f"Wikipedia: {title}",
                "snippet": combined_text,
                "url": f"https://en.wikipedia.org/wiki/{encoded_title}"
            })
            
    return evidence_items

def rank_by_relevance(items: list[dict], query: str) -> list[dict]:
    """Rank evidence passages by query token match score against snippet content."""
    clean_target = clean_question_query(query).lower()
    query_tokens = [w.lower() for w in re.findall(r'\w+', clean_target if clean_target else query) if len(w) > 2 and w.lower() not in ["the", "and", "for", "was", "were", "with", "that", "this", "where", "what", "located"]]
    
    def score(item):
        title = item.get("title", "").replace("Wikipedia:", "").lower()
        snippet = item.get("snippet", "").lower()
        match_score = 0
        if clean_target and clean_target in title:
            match_score += 10
        for tok in query_tokens:
            if tok in title:
                match_score += 3
            if tok in snippet:
                match_score += 1
        return match_score

    return sorted(items, key=score, reverse=True)

def search_wikipedia_passages(query: str, max_results: int = 4) -> list[dict]:
    """
    Search retriever: Fetch high-accuracy Wikipedia evidence passages.
    """
    evidence = search_wikipedia_engine(query)
    ranked = rank_by_relevance(evidence, query)
    return ranked[:max_results]

def search_wikipedia(query: str) -> str:
    items = search_wikipedia_passages(query, max_results=3)
    if not items:
        return "No evidence found."
    return "\n".join([f"[{item['title']}] ({item['url']}): {item['snippet']}" for item in items])
