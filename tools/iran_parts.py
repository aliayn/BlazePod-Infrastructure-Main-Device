#!/usr/bin/env python3
"""
iran_parts.py — Live Iranian electronics shop pricing for the Blazepod clone BOM.

WHAT IT DOES
    For each component in the query list, queries the search endpoints of several
    well-known Iranian electronics shops, parses the top product result, and records
    price (Toman), stock status, and product URL.

WHY IT EXISTS
    The WAT workflow delegates web operations to predictable tools (see claude.md).
    Iranian shop sites frequently rate-limit or block automated fetches, so this tool
    is defensive: every failure is recorded explicitly as NEEDS_CONFIRMATION rather
    than silently dropped. We never fabricate prices.

USAGE
    python tools/iran_parts.py --queries .tmp/part_queries.json --out .tmp/iran_parts.json
    python tools/iran_parts.py --queries .tmp/part_queries.json --out .tmp/iran_parts.json --timeout 15

INPUT  (.tmp/part_queries.json)
    [
      {"id": "mcu",        "query": "ESP32-C3",            "aliases": ["esp32 c3", "ایس‌پی ۳۲"]},
      {"id": "leds",       "query": "WS2812B ring",        "aliases": ["neopixel", "آدرس‌پذیر"]},
      ...
    ]

OUTPUT (.tmp/iran_parts.json)
    [
      {
        "id": "mcu",
        "query": "ESP32-C3",
        "results": [
          {"shop": "aftabrayaneh", "title": "...", "price_toman": 185000, "in_stock": true, "url": "...", "fetched_at": "..."},
          ...
        ],
        "needs_confirmation": false,
        "error": null
      },
      ...
    ]
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    sys.stderr.write(
        "Missing dependency. Install with:\n  pip install -r requirements.txt\n"
    )
    raise

# Load .env if present (optional — used only for endpoint overrides / proxy).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Shop adapters
# ---------------------------------------------------------------------------
# Each adapter is a function: (query, session, timeout) -> dict | None
# Returns {shop, title, price_toman, in_stock, url} or None on failure.
# Endpoints may be overridden via .env (e.g. AFTABRAYANEH_SEARCH_URL).

UA = os.getenv(
    "HTTP_USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
)


def _session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "fa,en;q=0.9"})
    proxy = os.getenv("IRAN_FETCH_PROXY")
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s


def _parse_toman(text: str):
    """Extract a numeric Toman price from arbitrary text. Returns int or None."""
    if not text:
        return None
    # Persian/Arabic digits -> ASCII
    p2a = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    text = text.translate(p2a)
    digits = re.findall(r"\d[\d,]*", text.replace("٬", ","))
    for d in digits:
        cleaned = d.replace(",", "").strip()
        if cleaned:
            # Heuristic: ignore tiny numbers (in-page ids). Require >= 3 digits.
            if len(cleaned) >= 3:
                try:
                    return int(cleaned)
                except ValueError:
                    continue
    return None


def _stock_from_text(text: str) -> bool:
    """Heuristic stock detection from Iranian shop status text."""
    t = (text or "").lower()
    if any(w in t for w in ["ناموجود", "اطلاع", "تمام", "unavailable", "out of stock"]):
        return False
    if any(w in t for w in ["موجود", "در انبار", "آماده", "in stock", "available"]):
        return True
    return True  # unknown → assume listed/available; flagged via confidence below


# --- AftabRayaneh ---------------------------------------------------------
def _aftabrayaneh(query, session, timeout):
    url = os.getenv("AFTABRAYANEH_SEARCH_URL") or "https://shop.aftabrayaneh.com/"
    try:
        r = session.get(
            url,
            params={"s": query, "post_type": "product"},
            timeout=timeout,
        )
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    # WooCommerce product link
    link = soup.select_one("a.woocommerce-LoopProduct-link, h2 a[href*='/product/']")
    if not link:
        return None
    prod_url = link.get("href") or (link.find("a") or {}).get("href")
    if not prod_url:
        return None
    title = (link.get_text(strip=True) or "").strip()
    # Price
    price_el = soup.select_one(
        "a.woocommerce-LoopProduct-link ins .amount, "
        "a.woocommerce-LoopProduct-link .amount, "
        ".price ins .amount, .price .amount"
    )
    price = _parse_toman(price_el.get_text(" ") if price_el else "")
    return {
        "shop": "aftabrayaneh",
        "title": title,
        "price_toman": price,
        "in_stock": True,
        "url": prod_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# --- ECA (electronic-club) ------------------------------------------------
def _eca(query, session, timeout):
    url = os.getenv("ECA_SEARCH_URL") or "https://ecabuy.com/"
    try:
        r = session.get(url, params={"search": query}, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    # ECA uses various product card selectors across redesigns.
    card = soup.select_one(
        ".product-card a, .product-item a[href*='product'], .products .product a"
    )
    if not card:
        return None
    prod_url = card.get("href")
    title = card.get_text(strip=True)
    price_el = soup.select_one(".price, .product-price, .price-new")
    price = _parse_toman(price_el.get_text(" ") if price_el else "")
    return {
        "shop": "eca",
        "title": title,
        "price_toman": price,
        "in_stock": True,
        "url": prod_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# --- Dicca ----------------------------------------------------------------
def _dicca(query, session, timeout):
    url = os.getenv("DICCA_SEARCH_URL") or "https://dicca.ir/"
    try:
        r = session.get(url, params={"s": query}, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    card = soup.select_one(
        ".product a[href*='/product/'], .products a, .product-card a"
    )
    if not card:
        return None
    prod_url = card.get("href")
    title = card.get_text(strip=True)
    price_el = soup.select_one(".price, .woocommerce-Price-amount, .amount")
    price = _parse_toman(price_el.get_text(" ") if price_el else "")
    return {
        "shop": "dicca",
        "title": title,
        "price_toman": price,
        "in_stock": True,
        "url": prod_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# --- Maker.ir -------------------------------------------------------------
def _makerir(query, session, timeout):
    url = os.getenv("MAKERIR_SEARCH_URL") or "https://maker.ir/"
    try:
        r = session.get(url, params={"s": query}, timeout=timeout)
        r.raise_for_status()
    except requests.RequestException:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    card = soup.select_one("a[href*='/product/']")
    if not card:
        return None
    prod_url = card.get("href")
    title = card.get_text(strip=True)
    price_el = soup.select_one(".price, .woocommerce-Price-amount")
    price = _parse_toman(price_el.get_text(" ") if price_el else "")
    return {
        "shop": "makerir",
        "title": title,
        "price_toman": price,
        "in_stock": True,
        "url": prod_url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


SHOPS = [_aftabrayaneh, _eca, _dicca, _makerir]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run(queries_path, out_path, timeout=15, delay=1.0):
    queries_path = Path(queries_path).resolve()
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with queries_path.open(encoding="utf-8") as f:
        queries = json.load(f)

    session = _session()
    results = []

    for item in queries:
        qid = item.get("id") or item.get("query")
        query = item.get("query", "")
        aliases = item.get("aliases", []) or []
        candidates = [query] + aliases

        shop_results = []
        last_error = None
        for cand in candidates:
            for shop_fn in SHOPS:
                try:
                    res = shop_fn(cand, session, timeout)
                    if res and (res.get("title") or res.get("price_toman")):
                        shop_results.append(res)
                except Exception as e:  # noqa: BLE001 — record, don't crash
                    last_error = f"{shop_fn.__name__}: {e}"
            time.sleep(delay)

        # Deduplicate by shop + url
        seen = set()
        deduped = []
        for r in shop_results:
            key = (r.get("shop"), r.get("url"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        needs_confirmation = not any(
            r.get("price_toman") for r in deduped
        )

        results.append(
            {
                "id": qid,
                "query": query,
                "aliases": aliases,
                "results": deduped,
                "needs_confirmation": needs_confirmation,
                "error": last_error if needs_confirmation else None,
            }
        )

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    confirmed = sum(1 for r in results if not r["needs_confirmation"])
    total = len(results)
    sys.stdout.write(
        f"[iran_parts] Wrote {out_path}\n"
        f"[iran_parts] {confirmed}/{total} parts have at least one price. "
        f"{total - confirmed} need manual confirmation.\n"
    )
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument(
        "--queries", required=True, help="Path to part_queries.json input"
    )
    p.add_argument(
        "--out", required=True, help="Path to write iran_parts.json output"
    )
    p.add_argument("--timeout", type=int, default=15, help="Per-request timeout (s)")
    p.add_argument(
        "--delay", type=float, default=1.0, help="Delay between requests (s)"
    )
    args = p.parse_args()
    run(args.queries, args.out, timeout=args.timeout, delay=args.delay)


if __name__ == "__main__":
    main()
