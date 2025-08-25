#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikipedia (wo.wikipedia.org) scraper — v2
- Utilise d'abord TextExtracts (prop=extracts) avec exlimit=max + exintro (meilleur taux)
- Si l'extract est vide, **fallback**: action=parse&prop=text (HTML) -> conversion texte (BeautifulSoup)
- Navigation via generator=allpages (namespace 0), pagination gérée
- Filtres: --prefix, --min-chars
- Sorties: JSONL (toujours) + CSV (optionnel)

Pourquoi ? Sur certains wikis/pages, TextExtracts renvoie parfois vide en mode generator.
Le combo exlimit=max + exintro aide, et on ajoute un fallback HTML pour garantir du texte.
"""

import argparse, time, sys, json
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
import pandas as pd
from bs4 import BeautifulSoup

API_URL_TMPL = "https://{lang}.wikipedia.org/w/api.php"

def build_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent.strip() or "npl-wolof-scraper/1.0 (mailto:odiop6170@gmail.com)",
        "Accept": "application/json"
    })
    return s

def fetch(session: requests.Session, lang: str, params: Dict[str, Any], retries: int = 5, backoff: float = 1.7) -> Dict[str, Any]:
    url = API_URL_TMPL.format(lang=lang)
    for attempt in range(1, retries + 1):
        r = session.get(url, params=params, timeout=30)
        if r.status_code in (429, 502, 503):
            ra = r.headers.get("Retry-After")
            wait = float(ra) if ra else (backoff ** attempt)
            time.sleep(min(wait, 60.0))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()

def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Retirer boîtes et éléments non textuels courants
    for sel in [
        ".infobox", ".navbox", ".metadata", ".reference", "table", "style", "script", ".mw-editsection"
    ]:
        for el in soup.select(sel):
            el.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Compactage
    return " ".join(text.split())

def normalize_text(txt: Optional[str]) -> str:
    if not txt:
        return ""
    return " ".join(txt.split())

def run(args):
    session = build_session(args.user_agent)

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "allpages",
        "gapnamespace": "0",
        "gapfilterredir": "nonredirects",
        "gaplimit": str(min(args.batch, 200)),
        "prop": "extracts",
        "explaintext": "1",
        "exintro": "1",     # aide TextExtracts avec generator
        "exlimit": "max",   # indispensable avec generator pour avoir des extracts multiples
        "exsectionformat": "plain",
    }
    if args.prefix:
        params["gapprefix"] = args.prefix

    kept = 0
    out_path = args.out
    seen = set()

    with open(out_path, "wb") as f:
        cont = None
        while True:
            if cont:
                params.update(cont)
            data = fetch(session, args.lang, params)

            pages: List[Dict[str, Any]] = data.get("query", {}).get("pages", [])
            if not pages and "continue" not in data:
                break

            for p in pages:
                pid = p.get("pageid")
                if not pid or pid in seen:
                    continue
                seen.add(pid)

                title = p.get("title")
                extract = normalize_text(p.get("extract", ""))

                # Fallback si extract vide -> action=parse (HTML) -> texte
                if not extract:
                    try:
                        parse_params = {
                            "action": "parse",
                            "format": "json",
                            "formatversion": "2",
                            "pageid": str(pid),
                            "prop": "text",
                            "disableeditsection": "1",
                            "disablelimitreport": "1",
                        }
                        parsed = fetch(session, args.lang, parse_params)
                        html = (parsed.get("parse") or {}).get("text") or ""
                        extract = extract_text_from_html(html)
                    except Exception as e:
                        extract = ""

                # Filtre longueur si demandé
                if args.min_chars and len(extract) < args.min_chars:
                    continue

                row = {
                    "pageid": pid,
                    "title": title,
                    "lang": args.lang,
                    "text": extract
                }
                f.write(json.dumps(row, ensure_ascii=False).encode("utf-8"))
                f.write(b"\n")
                kept += 1

                if args.limit and kept >= args.limit:
                    break

            if args.limit and kept >= args.limit:
                break

            cont = data.get("continue")
            if not cont:
                break
            time.sleep(args.sleep)

    print(f"[DONE] kept={kept}, file={out_path}", file=sys.stderr)

    if args.csv:
        df = pd.read_json(out_path, lines=True)
        df.to_csv(args.csv, index=False, encoding="utf-8")
        print(f"[DONE] CSV={args.csv}", file=sys.stderr)

def main():
    ap = argparse.ArgumentParser(description="Wikipedia scraper (wo) — TextExtracts + fallback HTML.")
    ap.add_argument("--lang", type=str, default="wo", help="Sous-domaine (wo, fr, en, ...)")
    ap.add_argument("--prefix", type=str, default=None, help="Filtrer les titres par préfixe (gapprefix).")
    ap.add_argument("--limit", type=int, default=5000, help="Nombre max d'articles.")
    ap.add_argument("--batch", type=int, default=100, help="Taille des lots API (<=200).")
    ap.add_argument("--min-chars", type=int, default=1, help="Filtrer les articles trop courts.")
    ap.add_argument("--sleep", type=float, default=0.4, help="Pause entre lots (s).")
    ap.add_argument("--user-agent", type=str, default="npl-wolof-scraper/1.0 (mailto:odiop6170@gmail.com)", help="UA descriptif.")
    ap.add_argument("--out", "-o", type=Path, default=Path("wowiki_v2.jsonl"), help="Sortie JSONL.")
    ap.add_argument("--csv", type=Path, default=None, help="Optionnel: CSV de sortie.")
    args = ap.parse_args()
    try:
        run(args)
    except requests.HTTPError as e:
        print(f"[HTTP ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
