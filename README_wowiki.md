# Wikipedia Wolof — Scraper via API

## Pourquoi tu as eu `403 Forbidden` ?
- Tu as probablement fait un `requests.get` direct sur la page HTML **sans User-Agent descriptif**.
- Wikimedia **recommande et peut exiger** un User-Agent clair avec un moyen de contact.
- Solution : soit **utiliser l'API officielle** (ce script), soit au minimum ajouter un header `User-Agent` quand tu fais un GET sur une page.

### Exemple minimal (page HTML FR avec UA)
```python
import requests
url = "https://fr.wikipedia.org/wiki/Wolof_(langue)"
headers = {"User-Agent": "npl-wolof/1.0 (mailto:odiop6170@gmail.com)"}
html = requests.get(url, headers=headers, timeout=30)
html.raise_for_status()
print(html.text[:500])
```

## Utiliser ce scraper (API) — recommandé
```powershell
python -m venv wiki
.\wiki\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements_wowiki.txt

# Récupérer 5000 articles (texte brut) du wiki wolof
python wowiki_scraper.py --limit 5000 --out wowiki.jsonl --csv wowiki.csv

# Récupérer seulement les titres commençant par 'a'
python wowiki_scraper.py --prefix a --limit 1000 -o a.jsonl

# Filtrer les articles < 200 caractères
python wowiki_scraper.py --min-chars 200 -o wowiki_clean.jsonl
```

## Pour des volumes énormes
- Télécharge les **dumps** sur https://dumps.wikimedia.org/wowiki/latest/ (ou autre langue) puis extrais le texte avec **WikiExtractor** :
```powershell
pip install wikiextractor
python -m wikiextractor --json --no_templates --output extracted wuwiki-*-pages-articles-multistream.xml.bz2
```
- C'est la méthode la plus stable/rapide pour de très gros corpus.
