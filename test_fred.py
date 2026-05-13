import requests

KEY = "e26710c24b9cd3247ab3c6e78c736cef"

# Procura séries PPI por país
searches = [
    ("Germany PPI",  "germany producer price"),
    ("France PPI",   "france producer price"),
    ("UK PPI",       "united kingdom producer price"),
    ("Japan PPI",    "japan producer price"),
    ("China PPI",    "china producer price"),
    ("Portugal PPI", "portugal producer price"),
    ("Spain PPI",    "spain producer price"),
    ("Italy PPI",    "italy producer price"),
]

for name, query in searches:
    url = (f"https://api.stlouisfed.org/fred/series/search"
           f"?search_text={query.replace(' ','%20')}"
           f"&api_key={KEY}&file_type=json&limit=3")
    r    = requests.get(url)
    data = r.json()
    sers = data.get("seriess", [])
    print(f"\n🔍 {name}:")
    for s in sers[:3]:
        print(f"   {s['id']:30} {s['title'][:60]}")