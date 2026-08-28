#!/usr/bin/env python3
"""
FORGE GROWTH META ADS LEAD ENGINE - GitHub Actions edition.
Resume mode: state.json tracks completed query batches + deep-scraped pages.
Every run does ONLY new work. Zero waste.
"""
import json
import re
import os
import sys
import time
import csv
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_FILE = os.path.join(OUT_DIR, "forge_meta_master.json")
MASTER_CSV = os.path.join(OUT_DIR, "forge_meta_master.csv")
STATE_FILE = os.path.join(OUT_DIR, "state.json")

API_KEYS = []
for env_name in ["APIFY_KEY0", "APIFY_KEY1", "APIFY_KEY2", "APIFY_KEY3",
                 "APIFY_KEY4", "APIFY_KEY5", "APIFY_KEY6", "APIFY_KEY7",
                 "APIFY_KEY8", "APIFY_KEY9"]:
    v = os.environ.get(env_name)
    if v:
        API_KEYS.append((v, env_name))
if not API_KEYS:
    raise RuntimeError("No APIFY_KEY* env vars set - configure GitHub secrets")

ACTOR = "code-node-tools~facebook-ad-library-scraper"

LARGE_BRANDS = ["jumia", "kong", "konga", "amazon", "ebay", "alibaba", "shein", "temu",
                "mtn", "airtel", "glo", "9mobile", "zenith", "gtbank", "access bank",
                "first bank", "ubea", "fidelity", "sterling", "paystack", "flutterwave",
                "interswitch", "moniepoint", "opay", "palm pay", "piggyvest", "kuda",
                "jiji", "kaymu", "slot", "pointek", "3c hub", "3chub"]

AGENCY_SIGNALS = ["marketing agency", "digital agency", "ads management", "media buying",
                  "ad agency", "growth agency", "social media agency", "media agency",
                  "performance marketing", "advertis", "agency", "boosting", "promoting page"]

BSP_SIGNALS = ["zendesk", "freshdesk", "intercom", "tidio", "hubspot", "livechat",
               "crisp", "chatwoot", "respond.io", "wati", "helpscout", "chatbot"]

NON_ECOM = ["hotel", "lodging", "logistics", "shipping", "airline", "university", "college",
            "school", "hospital", "clinic", "bank", "insurance", "travel agency", "travel",
            "real estate", "estate agent", "restaurant", "cafe", "church", "ngo", "ministry",
            "consultancy", "law firm", "pharmacy", "supermarket", "car dealer", "tourism",
            "safari", "immigration", "visa", "study abroad", "music", "movie", "film",
            "drama", "church", "gospel", "podcast", "radio", "news", "politics", "job",
            "recruitment", "crypto", "forex", "betting", "lottery", "loan", "mortgage",
            "dental", "medical", "health care", "wellness", "clinic",
            "media", "tv show", "entertainment", "production", "video",
            "design award", "award", "app", "software", "saas", "tool",
            "course", "training", "seminar", "webinar", "franchise",
            "affiliate", "high ticket", "high-ticket", "gadget wholesale",
            "distribution", "manufacturer", "b2b", "industrial"]

CATEGORY_KEYWORDS = ["fashion", "clothing", "boutique", "gadget", "phone", "electronics",
                     "beauty", "makeup", "skincare", "cosmetic", "dropship", "thrift",
                     "shoe", "sneaker", "handbag", "jewelry", "watch", "bag", "wig",
                     "hair", "accessor", "perfume", "fragrance", "smartphone", "laptop",
                     "tablet", "airpods", "earphone", "android", "iphone", "dress",
                     "ankara", "native wear", "agbada", "george", "lace", "t-shirt",
                     "hoodie", "jean", "gown", "koko", "makeup kit", "body cream",
                     "soap", "oil", "lash", "nail", "leather", "belt", "cap", "hat"]

NIGERIA_SIGNALS = ["nigeria", "lagos", "abuja", "kano", "ibadan", "port harcourt",
                   "enugu", "owerri", "benin city", "abia", "onitsha", "jos", "kaduna",
                   "sokoto", "zaria", "ilorin", "abeokuta", "akure", "uyo", "calabar",
                   "warri", "naira", "\u20a6", "9ja", "naija", "lag",
                   "wuse", "ikeja", "lekki", "ajah", "surulere", "yaba", "victoria island",
                   "gwarinpa", "kubwa", "garki", "utako", "festac", "egbeda", "ikeja"]

INSTA_FB_LINKS = ["instagram.com", "facebook.com", "fb.com", "m.me", "fb.me", "fb.watch",
                  "youtube.com", "youtu.be", "t.me", "telegram", "tiktok.com", "twitter.com",
                  "x.com", "snapchat", "pinterest", "linkedin", "whatsapp.com/channel"]

# ============ QUERY GENERATOR ============
PRODUCTS = [
    "fashion", "clothing", "boutique", "ankara", "native wear", "agbada",
    "thrift", "sneakers", "shoes", "handbag", "jewelry", "wig", "hair",
    "makeup", "skincare", "perfume", "dropship", "gadgets", "phone accessories",
    "electronics", "laptop", "smartwatch", "earpiece", "power bank",
    "dress", "gown", "suit", "shirt", "trouser", "jeans", "t-shirt",
    "leather bag", "backpack", "sunglasses", "watch", "belt", "cap",
    "body cream", "soap", "hair cream", "nail", "lash", "waist beads",
    "ankara bag", "beaded jewelry", "bridal gown", "engagement gown",
    "kids wear", "baby clothes", "polo", "joggers", "sportswear",
    "native cap", "gele", "headwrap", "scarf", "socks", "candle",
    "home decor", "kitchen", "bedding", "curtain", "furniture",
    "phone case", "charger", "cable", "car accessories", "bike",
    "air fryer", "blender", "iron", "generator", "fan", "tv",
    "glasses", "contact lens", "dental", "gym", "yoga", "dance",
    "asoebi bags", "bridal bag", "evening bag", "clutch bag",
    "ankara sneakers", "native shoes", "leather sandals",
    "agbada with cap", "senator wear", "two piece native",
    "kente print", "mudcloth", "adire fabric", "kampala fabric",
    "george silk", "brocade fabric", "chiffon gown",
    "sequin dress", "maxi gown", "off shoulder dress",
    "polo shirt Nigeria", "custom tshirt Lagos", "print tshirt",
    "joggers Nigeria", "cargo pants Lagos", "dungarees",
    "biker shorts", "leggings store", "tights Nigeria",
    "pajamas set", "nightwear Nigeria", "lingerie store Lagos",
    "swimwear Nigeria", "bikini store Lagos",
    "fitness wear Nigeria", "dance wear", "african print shoes",
    "wedding favors Nigeria", "party props Lagos", "birthday outfit",
    "corporate wear Nigeria", "office wear Lagos", "business casual",
    "school uniform supplier", "scrubs Nigeria", "nurse uniform",
    "apron store", "workwear Nigeria", "overalls Lagos",
    "raincoat Nigeria", "umbrella store Lagos", "socks store",
    "scarf Nigeria", "shawl Lagos", "pashmina",
    "hair clips", "headwrap Nigeria", "gele accessories",
    "jewelry box", "watch box", "sunglasses case",
    "perfume set Nigeria", "oils perfume", "attar Nigeria",
    "body spray Lagos", "deodorant store", "lipstick store",
    "eyeliner store", "eyeshadow palette", "foundation store",
    "nail polish Lagos", "manicure set", "pedicure tools",
    "hair dryer store", "straightener store", "curling iron",
    "wig cap", "wig stand", "hair net",
]

CITIES = [
    "Lagos", "Abuja", "Ibadan", "Kano", "Port Harcourt", "Enugu", "Benin City",
    "Aba", "Onitsha", "Owerri", "Warri", "Calabar", "Jos", "Kaduna", "Zaria",
    "Ilorin", "Abeokuta", "Akure", "Uyo", "Maiduguri", "Sokoto", "Bauchi",
    "Makurdi", "Minna", "Lokoja", "Nsukka", "Auchi", "Ogbomosho", "Osogbo",
    "Ado Ekiti", "Umuahia", "Awka", "Nnewi", "Asaba", "Ekpoma", "Suleja",
    "Keffi", "Lafia", "Gboko", "Katsina", "Dutse", "Gombe", "Yola",
    "Jalingo", "Damaturu", "Birnin Kebbi", "Gusau", "Kontagora",
]

def gen_queries():
    qs = []
    for p in PRODUCTS:
        qs.append(f"{p} Nigeria")
        qs.append(f"{p} Lagos")
    for p in PRODUCTS[:40]:
        for c in CITIES[:25]:
            qs.append(f"{p} {c}")
    seen = set()
    out = []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out

ALL_QUERIES = gen_queries()
MAX_SWEEPS_PER_RUN = int(os.environ.get("MAX_SWEEPS_PER_RUN", "6"))
MAX_DEEP_BATCHES_PER_RUN = int(os.environ.get("MAX_DEEP_BATCHES_PER_RUN", "20"))

# ============ STATE ============
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"done_queries": [], "deep_pages": [], "runs": 0}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def qhash(q):
    return hashlib.md5(q.encode()).hexdigest()[:10]

# ============ API ============
def api_get(url, key):
    last_err = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise
            last_err = e
            time.sleep(15)
        except Exception as e:
            last_err = e
            time.sleep(15)
    raise last_err

def api_request(url, key, data=None):
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode()
    last_err = None
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                raise
            last_err = e
            time.sleep(20)
        except Exception as e:
            last_err = e
            time.sleep(20)
    raise last_err

def key_usage(key):
    try:
        d = api_get(f"https://api.apify.com/v2/users/me/limits?token={key}", key)
        return d["data"]["current"]["monthlyUsageUsd"], d["data"]["limits"]["maxMonthlyUsageUsd"]
    except Exception:
        return None, None

def available_keys(min_remaining=0.30):
    """Return keys with budget remaining, most-remaining first."""
    usable = []
    for k, label in API_KEYS:
        used, lim = key_usage(k)
        if used is None:
            usable.append((k, label, 999))
            continue
        remaining = lim - used
        if remaining > min_remaining:
            usable.append((k, label, remaining))
    usable.sort(key=lambda x: -x[2])
    return usable

def run_actor(key, queries, limit_per_source, count, page_ids=None):
    url = f"https://api.apify.com/v2/acts/{ACTOR}/runs?token={key}"
    body = {
        "queries": queries,
        "countryCode": "NG",
        "limitPerSource": limit_per_source,
        "count": count,
        "scrapePageAds": {"activeStatus": "all", "countryCode": "NG"},
        "dedupe": True,
    }
    if page_ids:
        body["pageIds"] = page_ids
        body["queries"] = []
    return api_request(url, key, body)

def wait_run(key, run_id, timeout=900):
    start = time.time()
    while time.time() - start < timeout:
        try:
            d = api_request(f"https://api.apify.com/v2/actor-runs/{run_id}?token={key}", key)
            d = d["data"]
        except urllib.error.HTTPError:
            return {"status": "BLOCKED"}
        except Exception:
            time.sleep(10)
            continue
        if d["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return d
        time.sleep(10)
    return {"status": "TIMEOUT"}

def get_dataset(key, dataset_id):
    items = []
    offset = 0
    while True:
        url = (f"https://api.apify.com/v2/datasets/{dataset_id}/items"
               f"?token={key}&clean=true&format=json&offset={offset}&limit=1000")
        batch = api_get(url, key)
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return items

# ============ SCORING ============
def ad_duration_days(ad):
    start = ad.get("delivery_start_time")
    stop = ad.get("delivery_stop_time")
    try:
        s = datetime.fromisoformat(str(start).replace("Z", "+00:00")) if start else None
        e = datetime.fromisoformat(str(stop).replace("Z", "+00:00")) if stop else datetime.now(timezone.utc)
        if s:
            return (e - s).days
    except Exception:
        pass
    return None

def extract_link(ad):
    creatives = ad.get("creatives") or []
    for c in creatives:
        link = c.get("link_url") or ""
        if link:
            return link, c
    return "", (creatives[0] if creatives else {})

def is_whatsapp(link):
    return "wa.me" in link or "whatsapp" in link.lower() or "wa.link" in link

def is_landing_page(link):
    if not link:
        return False
    low = link.lower()
    if any(x in low for x in INSTA_FB_LINKS):
        return False
    return bool(re.match(r"^https?://", low))

def extract_whatsapp_number(link, text):
    m = re.search(r"(?:wa\.me|whatsapp\.com/send)(?:\?phone=|\/)(\d{9,15})", link)
    if m:
        return m.group(1)
    m = re.search(r"(\+?234[01]?\d{8,10})", text.replace(" ", ""))
    if m:
        return m.group(1)
    return None

def page_text(ad):
    parts = []
    for c in ad.get("creatives") or []:
        for k in ("body", "caption", "title", "cta_text"):
            if c.get(k):
                parts.append(str(c[k]))
    parts.append(ad.get("page", {}).get("name") or "")
    return " ".join(parts).lower()

def score_ad(ad):
    score = 0
    reasons = []
    flags = []
    link, creative = extract_link(ad)
    page = ad.get("page") or {}
    page_name = (page.get("name") or "").lower()
    likes = page.get("likes") or 0
    text = page_text(ad)
    wa_number = extract_whatsapp_number(link, text)

    if is_whatsapp(link):
        score += 30
        reasons.append("click-to-whatsapp")
    elif is_landing_page(link):
        score += 15
        reasons.append("website-landing-page")
    else:
        flags.append("not-whatsapp-or-website")

    cta = (creative.get("cta_type") or "").upper()
    cta_t = (creative.get("cta_text") or "").lower()
    if "SEND_MESSAGE" in cta or "whatsapp" in cta_t or "whatsapp" in text:
        score += 10
        reasons.append("whatsapp-cta")
    if wa_number:
        score += 5
        reasons.append(f"wa:{wa_number}")

    days = ad_duration_days(ad)
    if days is not None and days >= 14:
        score += 15
        reasons.append(f"active-{days}d")
    elif days is not None and days <= 3:
        flags.append("one-off-ad")
        score -= 15

    nigeria_hits = [s for s in NIGERIA_SIGNALS if s in text or s in page_name]
    if nigeria_hits:
        score += 10
        reasons.append("ng-cues:" + ",".join(nigeria_hits[:3]))

    cat_hits = [s for s in CATEGORY_KEYWORDS if s in text or s in page_name]
    if cat_hits:
        score += 8
        reasons.append("category:" + ",".join(cat_hits[:3]))

    if likes == 0:
        score += 6
        reasons.append("unknown-size")
    elif likes < 50000:
        score += 8
        reasons.append(f"small-mid-{likes}")
    elif likes > 500000:
        score -= 20
        flags.append("large-enterprise")

    if any(b in page_name or b in text for b in LARGE_BRANDS):
        score -= 40
        flags.append("large-brand")
    if any(a in text for a in AGENCY_SIGNALS):
        score -= 25
        flags.append("agency-account")
    if any(b in text for b in BSP_SIGNALS):
        score -= 15
        flags.append("uses-bsp")
    if any(n in text for n in NON_ECOM):
        score -= 30
        flags.append("non-ecom")

    if re.search(r"[\u20a6]\s?\d|naira|#\s?\d{2,}|N\s?\d{2,}", text):
        score += 12
        reasons.append("naira-pricing")

    is_active = ad.get("is_active")
    if is_active is False:
        score -= 20
        flags.append("inactive-ad")

    return score, reasons, flags, wa_number

# ============ MASTER ============
def load_master():
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE) as f:
            return json.load(f).get("leads", {})
    return {}

def save_master(leads):
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    with open(MASTER_FILE, "w") as f:
        json.dump({"updated": datetime.now().isoformat(), "count": len(leads), "leads": leads},
                  f, indent=2, default=str)
    fields = ["page_name", "page_url", "likes", "link_url", "whatsapp_number", "duration_days",
              "publisher_platforms", "delivery_start", "delivery_stop", "ad_body", "ad_image",
              "score", "reasons", "flags", "page_id", "ad_id", "collected_at"]
    with open(MASTER_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for l in sorted(leads.values(), key=lambda x: -x.get("score", 0)):
            w.writerow(l)
    snap = os.path.join(OUT_DIR, f"forge_meta_snapshot_{ts}.csv")
    with open(snap, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for l in sorted(leads.values(), key=lambda x: -x.get("score", 0)):
            w.writerow(l)
    return snap

def process_ads(ads, leads, pool=None):
    new_pages = 0
    new_ads = 0
    for ad in ads:
        link, creative = extract_link(ad)
        page = ad.get("page") or {}
        pid = str(page.get("id") or ad.get("id"))
        if pool is not None:
            pool[pid] = {"page_id": pid, "page_name": page.get("name"),
                         "page_url": page.get("page_url"), "likes": page.get("likes")}
        if not (is_whatsapp(link) or is_landing_page(link)):
            continue
        score, reasons, flags, wa_number = score_ad(ad)
        entry = {
            "ad_id": ad.get("id"),
            "page_id": pid,
            "page_name": page.get("name"),
            "page_url": page.get("page_url"),
            "likes": page.get("likes"),
            "verified": page.get("verified"),
            "is_active": ad.get("is_active"),
            "link_url": link,
            "whatsapp_number": wa_number,
            "ad_body": (creative.get("body") or "")[:800] if creative.get("body") else "",
            "ad_image": creative.get("image_url") or "",
            "publisher_platforms": ad.get("publisher_platforms"),
            "delivery_start": ad.get("delivery_start_time"),
            "delivery_stop": ad.get("delivery_stop_time"),
            "duration_days": ad_duration_days(ad),
            "collected_at": ad.get("collected_at"),
            "score": score,
            "reasons": ", ".join(reasons),
            "flags": ", ".join(flags),
        }
        if pid in leads:
            if score > leads[pid]["score"]:
                leads[pid] = entry
                new_ads += 1
        else:
            leads[pid] = entry
            new_pages += 1
    return new_pages, new_ads

# ============ SWEEP (resume-aware) ============
def sweep_with_key(key, label, queries, limit_per_source=20, count=400, page_ids=None):
    """Run one actor call; returns raw ads or None if blocked."""
    try:
        run = run_actor(key, queries, limit_per_source, count, page_ids=page_ids)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print(f"  !! {label} blocked ({e.code})")
            return None
        print(f"  !! {label} error {e.code}")
        return None
    run_id = run["data"]["id"]
    dataset_id = run["data"]["defaultDatasetId"]
    result = wait_run(key, run_id)
    if result.get("status") != "SUCCEEDED":
        print(f"  !! run {result.get('status')}")
        return None
    return get_dataset(key, dataset_id)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    leads = load_master()
    state = load_state()
    state["runs"] = state.get("runs", 0) + 1
    print(f"Run #{state['runs']} | master: {len(leads)} pages | done queries: {len(state['done_queries'])} | deep pages: {len(state['deep_pages'])}")

    hard_reject = ["large-brand", "agency-account", "not-whatsapp-or-website", "non-ecom", "large-enterprise"]
    pool = {}

    keys = available_keys()
    print(f"Available keys with budget: {len(keys)}")
    if not keys:
        print("NO BUDGET LEFT - exiting")
        save_state(state)
        return

    # ---- Phase 1: run UNDONE queries (resume-aware) ----
    undone = [q for q in ALL_QUERIES if qhash(q) not in set(state["done_queries"])]
    print(f"Undone queries: {len(undone)} / {len(ALL_QUERIES)}")

    chunks = [undone[i:i+60] for i in range(0, len(undone), 60)]
    sweeps_done = 0
    ki = 0

    for ci, chunk in enumerate(chunks):
        if sweeps_done >= MAX_SWEEPS_PER_RUN:
            print("Sweep budget for this run reached")
            break
        if ki >= len(keys):
            keys = available_keys()
            ki = 0
            if not keys:
                print("No more budget")
                break
        key, label, _ = keys[ki]
        ki += 1

        print(f"\nSWEEP {ci+1}/{len(chunks)} | {label} | {len(chunk)} new queries")
        ads = sweep_with_key(key, label, chunk, limit_per_source=20, count=400)
        if ads is None:
            continue
        sweeps_done += 1
        np_, na = process_ads(ads, leads, pool=pool)
        for q in chunk:
            state["done_queries"].append(qhash(q))
        print(f"  -> +{np_} new pages, {na} upgraded | master {len(leads)} | pool {len(pool)}")
        save_master(leads)
        save_state(state)
        time.sleep(120)

    # ---- Phase 2: deep-scrape UNDONE pool pages ----
    to_deep = [pid for pid in pool.keys() if pid not in set(state["deep_pages"])]
    print(f"\nPool: {len(pool)} pages | to deep-scrape: {len(to_deep)}")
    deep_done = 0
    ki = 0

    for j in range(0, len(to_deep), 20):
        if deep_done >= MAX_DEEP_BATCHES_PER_RUN:
            print("Deep budget for this run reached")
            break
        if ki >= len(keys):
            keys = available_keys()
            ki = 0
            if not keys:
                print("No more budget")
                break
        key, label, _ = keys[ki]
        ki += 1

        batch_ids = to_deep[j:j+20]
        print(f"\nDEEP {j//20+1}/{len(to_deep)//20+1} | {label} | {len(batch_ids)} pages")
        ads = sweep_with_key(key, label, [], limit_per_source=100, count=len(batch_ids) * 100, page_ids=batch_ids)
        if ads is None:
            continue
        deep_done += 1
        np_, na = process_ads(ads, leads, pool=pool)
        for pid in batch_ids:
            state["deep_pages"].append(pid)
        print(f"  -> {len(ads)} ads | +{np_} new pages, {na} upgraded | master {len(leads)}")
        save_master(leads)
        save_state(state)
        time.sleep(60)

    # ---- Final: recompute qualified ----
    qualified = {k: v for k, v in leads.items() if not any(f in v["flags"] for f in hard_reject)}
    qualified = dict(sorted(qualified.items(), key=lambda x: -x[1]["score"]))
    snap = save_master(leads)
    save_state(state)

    print(f"\n{'='*60}")
    print(f"RUN COMPLETE | master: {len(leads)} | qualified: {len(qualified)}")
    print(f"Done queries: {len(state['done_queries'])}/{len(ALL_QUERIES)}")
    print(f"Deep pages: {len(state['deep_pages'])}")
    print(f"Snapshot: {snap}")
    print(f"{'='*60}")

    if os.environ.get("SHOW_TOP") == "1":
        print("\n=== TOP 30 QUALIFIED ===")
        for i, (pid, l) in enumerate(qualified.items()):
            if i >= 30:
                break
            wa = f" wa:{l['whatsapp_number']}" if l.get("whatsapp_number") else ""
            print(f"  [{l['score']:+3d}] {str(l['page_name'])[:30]:30} | {str(l['link_url'])[:38]:38} | {l.get('duration_days')}d{wa}")

if __name__ == "__main__":
    main()
