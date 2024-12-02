# Collecte de livres

## Installation

Soit juste avec pip:

```bash
pip install https://github.com/arnaud-ma/projet-poo
```

Ou en clonant le dépôt:

```bash
git clone https://github.com/arnaud-ma/projet-poo
cd projet-poo
pip install .
```

Pour de nombreux formats, il est nécessaire d'installer [`pandoc`](https://pandoc.org/installing.html) pour convertir les fichiers.

## Utilisation

### Créer une bibliothèque

```python
import biblio

b = biblio.bibli("mon_repertoire/")
```

`b` agit comme un `set` de `Livre`. Mais lorsqu'on ajoute ou on supprime un livre, le repertoire est mis à jour. On peut ajouter un livre de deux façons:

```python
# un fichier local
b.ajouter("mon_livre.pdf")

# un fichier en ligne
b.alimenter_fichier_url("https://url.com/mon_livre.pdf")

# tous les livres d'une page en ligne
b.alimenter("https://url.com/")
```

Pour le scraping:

```python
b = bibli_scrap("mon_repertoire/")
b.scrap("https://url.com/", profondeur=3, nbmax=100, ...)
```

Où la profondeur représente le nombre de liens à suivre,
et `nbmax` le nombre de livres à récupérer. Les autres arguments sont
tous ceux de `requests.get`, pour effectuer une requête HTTP (comme `headers` ou `verify`).

### Rapports

```python
b.rapport_livres("pdf", "mon_rapport.pdf")
```

Les formats disponibles, autant pour les livres que pour les rapports, sont listés dans `biblio.FORMATS_DISPONIBLES`.

### Créer un nouveau format

Pour ajouter un nouveau format, il suffit de créer une classe héritant de `Livre` :*

```python
class MonFormat(Livre, suffix=".mon", mime_type="application/mon"):
    ...
```

Les paramètres `suffix` et `mime_type` sont obligatoires.

La classe doit implémenter les méthodes suivantes:

- `auteurs(self) -> list[str]`: les auteurs du livre. Il est possible de retourner une liste vide ou avec un seul élément.
- `titre(self) -> str`: le titre du livre.
- `langue(self) -> str`: la langue du livre.
- `sujets(self) -> list[str]`: les sujets du livre. Il est possible de retourner une liste vide ou avec un seul élément.
- `date_obj(self) -> datetime.date`: la date de publication du livre sous forme d'objet `datetime.date`.
- `write_from_markdown(self, content: str)`: écrire un livre au format `MonFormat` à partir d'une chaîne de caractères en markdown.

Les autre méthode disponibles sont:

- `sujet()` et `auteur()` qui retournent respectivement tous les sujets et auteurs du livre listés avec des virgules.
- `date(fmt="%d/%m/%Y")` qui retourne la date de publication sous forme de chaîne de caractères formatée.

La documentation en epub a elle-même été généré avec le module `biblio`:

```python
from pathlib import Path
import biblio
biblio.Epub("README.pdf").write_from_markdown(Path("README.md").read_text(encoding="utf-8"))
```
