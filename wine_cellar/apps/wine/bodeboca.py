import requests

ALGOLIA_APP_ID = "5C8NIYBJF4"
ALGOLIA_API_KEY = "eb7c7bf42d6779fb9f276417f2f2a879"
ALGOLIA_INDEX = "store_1_role_authenticated"
_ALGOLIA_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes/{ALGOLIA_INDEX}/query"


def search_wines(query, vintage=None, hits_per_page=6):
    headers = {
        "X-Algolia-Application-Id": ALGOLIA_APP_ID,
        "X-Algolia-API-Key": ALGOLIA_API_KEY,
    }
    body = {
        "query": query,
        "hitsPerPage": hits_per_page,
        "attributesToRetrieve": ["es", "image_url", "vintage", "winery"],
    }
    if vintage:
        body["filters"] = f"vintage={vintage}"

    resp = requests.post(_ALGOLIA_URL, json=body, headers=headers, timeout=5)
    resp.raise_for_status()

    results = []
    for h in resp.json().get("hits", []):
        if not h.get("image_url"):
            continue
        es = h.get("es", {})
        results.append({
            "title": es.get("title", ""),
            "image_url": h["image_url"],
            "vintage": h.get("vintage"),
            "url": "https://www.bodeboca.com" + es.get("path", ""),
        })
    return results
