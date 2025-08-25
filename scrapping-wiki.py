import requests
from bs4 import BeautifulSoup
import csv

url = "https://fr.wikipedia.org/wiki/Wolof_(langue)"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/139.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

mots_wolof = set()

# On cible les tableaux de vocabulaire
tables = soup.find_all('table', {'class': 'wikitable'})

for table in tables:
    rows = table.find_all('tr')
    for row in rows[1:]:  # on saute l'en-tête
        cols = row.find_all(['td', 'th'])
        if len(cols) >= 2:  # au moins 2 colonnes
            wolof_text = cols[1].get_text(strip=True)
            # Nettoyage : on enlève les parenthèses et notes
            wolof_text = wolof_text.split('(')[0].strip()
            if wolof_text:
                mots_wolof.add(wolof_text)

# Écriture CSV
with open('mots_wolof.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['mot_wolof'])
    for mot in sorted(mots_wolof):
        writer.writerow([mot])

print(f"Extraction terminée ! {len(mots_wolof)} mots wolof sauvegardés dans mots_wolof.csv")
