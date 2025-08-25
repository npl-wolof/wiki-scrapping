#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wikipedia Wolof (wo.wikipedia.org) scraper via MediaWiki Action API.
- Parcourt tous les articles (namespace 0) avec generator=allpages
- Récupère le texte brut (prop=extracts&explaintext)
- Gère la pagination (gapcontinue) et un backoff simple
- Sauvegarde en JSONL (+ CSV optionnel)

USAGE EXEMPLES (Windows PowerShell) :
  python wowiki_scraper.py --limit 5000 --out wowiki.jsonl --csv wowiki.csv
  python wowiki_scraper.py --prefix a --limit 1000 -o a.jsonl
  python wowiki_scraper.py --lang wo --min-chars 200 --out wowiki_clean.jsonl

CONSEILS :
- Utilisez un User-Agent descriptif avec contact (bonnes pratiques Wikimedia).
- Pour du scraping massif, préférez les dumps officiels + WikiExtractor (voir README).

Auteur : adapté pour Omar DIOP (npl_wolof)
"""

import argparse
import time
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
import pandas as pd

API_URL_TMPL = "https://{lang}.wikipedia.org/w/api.php"

def build_session(user_agent: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": user_agent.strip() or "npl-wolof-scraper/1.0 (+contact: example@example.com)",
        "Accept": "application/json"
    })
    return s

def fetch_batch(session: requests.Session, lang: str, params: Dict[str, Any], retries: int = 5, backoff: float = 1.5) -> Dict[str, Any]:
    url = API_URL_TMPL.format(lang=lang)
    for attempt in range(1, retries + 1):
        r = session.get(url, params=params, timeout=30)
        # gestion de rate limit / erreurs transitoires
        if r.status_code in (429, 503, 502):
            ra = r.headers.get("Retry-After")
            wait = float(ra) if ra else (backoff ** attempt)
            time.sleep(min(wait, 60.0))
            continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()  # si on sort de la boucle avec une erreur persistante

def normalize_text(txt: Optional[str]) -> str:
    if not txt:
        return ""
    # nettoyage léger
    return " ".join(txt.split())

def run(args):
    session = build_session(args.user_agent)

    # paramètres de base pour generator=allpages
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "generator": "allpages",
        "gapnamespace": "0",            # articles principaux uniquement
        "gapfilterredir": "nonredirects",
        "gaplimit": str(min(args.batch, 200)),  # limite par batch (max 500 généralement)
       "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
    }
    if args.prefix:
        params["gapprefix"] = args.prefix

    out_path = args.out
    kept = 0
    seen_ids = set()

    with open(out_path, "wb") as f:
        cont = None
        while True:
            if cont:
                params.update(cont)  # gapcontinue + continue
            data = fetch_batch(session, args.lang, params)

            pages: List[Dict[str, Any]] = data.get("query", {}).get("pages", [])
            if not pages and "continue" not in data:
                break

            for p in pages:
                pid = p.get("pageid")
                title = p.get("title")
                extract = normalize_text(p.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("*", ""))

                if not pid or not title:
                    continue

                if args.min_chars and len(extract) < args.min_chars:
                    continue

                if pid in seen_ids:
                    continue
                seen_ids.add(pid)

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

            # pagination
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
    ap = argparse.ArgumentParser(description="Scraper Wikipedia via API (wolof par défaut).")
    ap.add_argument("--lang", type=str, default="wo", help="Sous-domaine Wikipedia (ex: wo, fr, en).")
    ap.add_argument("--prefix", type=str, default=None, help="Option: lettre/préfixe de titre (gapprefix).")
    ap.add_argument("--limit", type=int, default=5000, help="Nombre maximum d'articles à récupérer.")
    ap.add_argument("--batch", type=int, default=100, help="Taille d'un lot API (<=200).")
    ap.add_argument("--min-chars", type=int, default=0, help="Filtrer les articles trop courts.")
    ap.add_argument("--sleep", type=float, default=0.5, help="Pause entre lots (s).")
    ap.add_argument("--user-agent", type=str, default="npl-wolof-scraper/1.0 (mailto:odiop6170@gmail.com)", help="UA descriptif avec contact.")
    ap.add_argument("--out", "-o", type=Path, default=Path("wowiki.jsonl"), help="Fichier de sortie JSONL.")
    ap.add_argument("--csv", type=Path, default=None, help="Optionnel: fichier CSV de sortie.")
    args = ap.parse_args()
    try:
        run(args)
    except requests.HTTPError as e:
        print(f"[HTTP ERROR] {e} — Vérifiez votre User-Agent et vos paramètres.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
