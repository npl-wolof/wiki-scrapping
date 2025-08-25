# Corpus Wolof – Scraping Wikipédia pour NLP

Ce projet a pour objectif de **constituer un corpus en langue Wolof** à partir de Wikipédia (`wo.wikipedia.org`) pour des travaux de **Natural Language Processing (NLP)**, incluant la récupération de mots, expressions et articles complets.

---

## Table des matières

1. [Présentation](#présentation)  
2. [Scripts utilisés](#scripts-utilisés)  
3. [Workflow de scraping](#workflow-de-scraping)  
4. [Installation et dépendances](#installation-et-dépendances)  
5. [Exécution](#exécution)  
6. [Fichiers générés](#fichiers-générés)  
7. [Bonnes pratiques](#bonnes-pratiques)  
8. [Conseils pour NLP](#conseils-pour-nlp)  
9. [Auteur](#auteur)  

---

## Présentation

Wikipédia Wolof est limité en contenu, et certains articles n'ont pas de texte extractible directement. Ce projet combine trois approches pour maximiser la récupération de données :

1. **Scraping direct des pages en français** pour extraire les mots Wolof listés dans les tableaux de vocabulaire.  
2. **API MediaWiki (`generator=allpages`)** pour récupérer les articles complets en wikitext.  
3. **Version améliorée avec fallback HTML** pour garantir le texte même si `prop=extracts` est vide.

Le corpus obtenu permet d’alimenter des modèles NLP pour :

- Analyse lexicale et morphologique.  
- Création de dictionnaires.  
- Applications de traduction ou NLP Wolof.

---

## Scripts utilisés

### 1. `scrape_vocab_wolof.py`
- Scraping direct depuis la page Wikipédia **française** sur la langue Wolof.  
- Utilise **BeautifulSoup** pour extraire les mots dans les tableaux.  
- Sauvegarde en CSV (`mots_wolof.csv`) avec une colonne `mot_wolof`.  

**Usage :**
```bash
python scrape_vocab_wolof.py
```
2. wowiki_scraper.py

Scraping via l’API MediaWiki pour récupérer le wikitext complet (prop=revisions).

Filtrage par préfixe de titre (--prefix) et longueur minimum (--min-chars).

Sauvegarde en JSONL et optionnellement en CSV.

Usage :

python wowiki_scraper.py --limit 5000 --out wowiki.jsonl --csv wowiki.csv

3. wowiki_scraper_v2.py

Version améliorée : récupère d’abord prop=extracts et, en cas de texte vide, fait un fallback HTML (action=parse) converti en texte avec BeautifulSoup.

Assure la récupération maximale du contenu.

Sortie JSONL + CSV optionnel.

Usage :

python wowiki_scraper_v2.py --limit 5000 --out wowiki_v2.jsonl --csv wowiki_v2.csv

Workflow de scraping

Récupération lexicale (français → Wolof)

Extraire les tableaux de vocabulaire → CSV mots_wolof.csv.

Récupération articles Wolof (API MediaWiki)

generator=allpages → prop=revisions → JSONL wowiki.jsonl.

Fallback HTML pour articles vides

prop=extracts → si vide, action=parse → conversion HTML → JSONL wowiki_v2.jsonl.

Conversion optionnelle en CSV pour exploitation simple.

Installation et dépendances

Cloner le dépôt :

git clone <URL_DU_DEPOT>
cd wiki


Créer un environnement virtuel :

python -m venv venv
# Linux / Mac
source venv/bin/activate
# Windows
venv\Scripts\activate


Installer les dépendances :

pip install -r requirements.txt


Ignorer le venv dans Git :

# Ignorer l'environnement virtuel
venv/

Exécution
Exemples de commandes :

Scraping vocabulaire :

python scrape_vocab_wolof.py


Scraping articles Wolof (limite 5000) :

python wowiki_scraper.py --limit 5000 --out wowiki.jsonl --csv wowiki.csv


Scraping amélioré avec fallback HTML :

python wowiki_scraper_v2.py --limit 5000 --out wowiki_v2.jsonl --csv wowiki_v2.csv


Filtrer par préfixe et longueur minimale :

python wowiki_scraper_v2.py --prefix A --min-chars 200 --out wowiki_v2.jsonl