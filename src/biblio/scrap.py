import logging
import re
import urllib
import urllib.parse
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup

from biblio.bibli import simple_bibli
from biblio.livre import Livre

logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def check_response(response):
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        msg = f"Erreur HTTP: {e}"
        logger.exception(msg)
        return False
    except requests.exceptions.Timeout as e:
        msg = f"Timeout: {e}"
        logger.exception(msg)
        return False
    except Exception as e:
        msg = f"Erreur inconnue lors de la récupération de la page: {e}"
        logger.exception(msg)
        return False
    return True


class bibli(simple_bibli):

    def find_unique_path(self, path: Path) -> Path:
        stem = path.stem
        filenames = set(self.path.iterdir())
        i = 1
        while path in filenames:
            path = path.with_stem(f"{stem}_{i}")
            i += 1
        return path

    @staticmethod
    def check_http_url(url, *, ignore_log=False):
        if not url.startswith(("http:", "https:")):
            if not ignore_log:
                msg = f"L'URL doit commencer par http: ou https: (url={url})"
                logger.error(msg)
            return False
        return True

    @staticmethod
    def get_mime_type_from_url(url, *args, **kwargs):
        response = requests.head(url, *args, timeout=5, **kwargs)
        mime_type = response.headers.get("Content-Type")
        if mime_type not in Livre.TYPES_MIME:
            return None
        return mime_type

    def alimenter_fichier_url(self, url, *, verify=True, ignore_log=False):
        if not self.check_http_url(url, ignore_log=ignore_log):
            return

        # récupération du type MIME
        mime_type = self.get_mime_type_from_url(url, verify=verify)
        if mime_type is None:
            if not ignore_log:
                msg = f"Type MIME non supporté pour l'URL {url}"
                logger.error(msg)
            return

        # récupération du fichier
        # puis trouver un nom de fichier unique pour le stocker
        # et enfin créer un objet Livre correspondant
        response = requests.get(url, timeout=5, verify=verify)
        url_parsed = urllib.parse.urlparse(url)
        filename = Path(url_parsed.path).name
        path_livre = self.find_unique_path(Path(self.path) / filename)
        path_livre.write_bytes(response.content)
        livre = Livre.depuis_mime_type(mime_type)(path_livre)
        self.ajouter(livre)

    @staticmethod
    def livre_generator_from_url(url, *, verify=True):
        response = requests.get(url, timeout=5, verify=verify)
        if not check_response(response):
            return
        soup = BeautifulSoup(response.content, "html.parser")

        def join_url(a):
            return urllib.parse.urljoin(url, a["href"])

        yield from map(join_url, soup.find_all("a", href=True))

    def alimenter(self, url, *, verify=True):
        for url_livre in self.livre_generator_from_url(url, verify=verify):
            self.alimenter_fichier_url(url_livre, verify=verify)


def main():
    biblio = bibli("temp/")
    biblio.alimenter(
        "https://math.univ-angers.fr/~jaclin/biblio/livres/",
        verify=False,
    )
    biblio.rapport_livres("pdf", "rapport.pdf")


if __name__ == "__main__":
    main()


class bibli_scrap(bibli):
    def __init__(self, url, profondeur=3, nbmax=100):
        self.url = [url]
        self.url_visiter = []
        self.profondeur = profondeur
        self.nbmax = nbmax

    def get_html(self, source):
        # ouverture et demande les documents html de la page
        reponse = requests.get(source, timeout=5)

        # je verifie si la page est bien ouverte
        try:
            reponse.raise_for_status()
        except requests.exceptions.HTTPError as e:
            msg = f"Erreur HTTP: {e}"
            logger.exception(msg)
            return None
        except requests.exceptions.Timeout as e:
            msg = f"Timeout: {e}"
            logger.exception(msg)
            return None
        except Exception as e:
            msg = f"Erreur inconnue lors de la récupération de la page: {e}"
            logger.exception(msg)
            return None

        # je recupere le contenu de la page
        return BeautifulSoup(reponse.content, "html.parser")

    """je recupere le nom du domaine du site"""
    def domaine_site(self, url):
        return re.search(r"w?[a-v|x-z][\w%\+-\.]+\.(org|fr|com|net)", url).group()

    def get_lien_url(self, url):
        soup = self.get_Html(url)
        domaine = self.domaine_site(url)

        for lien in soup.find_all("a", attrs={"href": re.compile(r"^https://")}):
            if ((domaine and "pdf") in lien.get("href", [])) or (
                (domaine and "epub") in lien.get("href", [])
            ):
                self.add_url(lien.get("href"))

    def add_url(self, lien):
        if lien not in self.url and lien not in self.url_visiter:
            self.url.append(lien)

    """je parcour le nombre maximal de lien pour les scroler"""

    def parcourir(self):
        while self.url and len(self.url_visiter) < self.profondeur:
            url = self.url[0]
            try:
                self.get_lien_url(url)
                self.url_visiter.append(url)
            except AttributeError:
                print(f"nous ne peuvont pas scroler {url}")

    """je telecharge les fichiers

    PS: JE N'EST PAS EN TESTER LA FONCTION TELEGHARGER
    """

    def telecharger(self):
        for i in self.url_visiter:
            # je recuper les attribues du livre
            nom_livrres = self.get_Html(i).find("p", class_="Libros_Titulo").text
            if "pdf" in i:
                attribue = ".pdf"
            else:
                attribue = ".epub"

            # télécharge le fichier
            response = requests.get(i.get("href"))

            # sauvgarder le fichier
            pdf = open(nom_livrres + str(i) + attribue, "wb")
            pdf.write(response.content)
            pdf.close()
            print("File ", i, " downloaded")


# bibli_scrap(
#     "https://infolivres.org/livres-gratuits-pdf/histoire/histoire-de-rome/",
# ).parcourir()
