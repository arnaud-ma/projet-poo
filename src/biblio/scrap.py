import logging
import urllib
import urllib.parse
from pathlib import Path
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

from biblio.bibli import simple_bibli
from biblio.livre import Livre

logger = logging.getLogger(__name__)
MIME_HTML = "text/html"

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
        return response.headers.get("Content-Type")

    def gen_url_mime_from_url(self, url, *args, **kwargs):
        response = requests.get(url, *args, timeout=5, **kwargs)
        if not check_response(response):
            return
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.find_all("a", href=True):
            url_full = urljoin(url, a["href"])
            mime = self.get_mime_type_from_url(url_full, *args, **kwargs)
            if mime is not None:
                yield (url_full, mime)

    def alimenter_fichier_url(
        self,
        url,
        type_mime=None,
        *args,
        ignore_log=False,
        **kwargs,
    ):
        if not self.check_http_url(url, ignore_log=ignore_log):
            return

        # récupération du type MIME
        if type_mime is None:
            type_mime = self.get_mime_type_from_url(url, *args, **kwargs)
            if type_mime not in Livre.TYPES_MIME:
                if not ignore_log:
                    msg = f"Type MIME non supporté pour l'URL {url}"
                    logger.error(msg)
                return

        # récupération du fichier
        # puis trouver un nom de fichier unique pour le stocker
        # et enfin créer un objet Livre correspondant
        response = requests.get(url, *args, timeout=5, **kwargs)
        url_parsed = urllib.parse.urlparse(url)
        filename = Path(url_parsed.path).name
        path_livre = self.find_unique_path(Path(self.path) / filename)
        path_livre.write_bytes(response.content)
        livre = Livre.depuis_mime_type(type_mime)(path_livre)
        self.ajouter(livre)

    def livre_generator_from_url(self, url, *args, **kwargs):
        for url_livre, mime in self.gen_url_mime_from_url(url, *args, **kwargs):
            if mime in Livre.TYPES_MIME:
                yield (url_livre, mime)

    def alimenter(self, url, *args, **kwargs):
        for url_livre, mime in self.livre_generator_from_url(url, *args, **kwargs):
            self.alimenter_fichier_url(url_livre, *args, type_mime=mime, **kwargs)


class bibli_scrap(bibli):
    def url_generator_from_url(self, url, *args, **kwargs):
        response = requests.get(url, *args, timeout=5, **kwargs)
        if not check_response(response):
            return
        soup = BeautifulSoup(response.content, "html.parser")
        for a in soup.find_all("a", href=True):
            full_url = urljoin(url, a["href"])
            mime = self.get_mime_type_from_url(full_url, *args, **kwargs)
            if mime is not None and MIME_HTML in mime:
                yield full_url

    def scrap_livre_generator(
        self, url, profondeur=3, nbmax=100, *args, ignore_log=False, **kwargs
    ):
        def dfs(url, profondeur_actuelle):
            nonlocal compteur_livres
            if profondeur_actuelle > profondeur:
                return
            if url in visited:
                return
            visited.add(url)
            try:
                for url_, mime in self.gen_url_mime_from_url(url, *args, **kwargs):
                    if mime in Livre.TYPES_MIME:
                        compteur_livres += 1
                        yield (url_, mime)
                        if compteur_livres >= nbmax:
                            return
                    elif MIME_HTML in mime:
                        if url_ not in visited:
                            yield from dfs(url_, profondeur_actuelle + 1)
            except Exception as e:
                if not ignore_log:
                    msg = f"Erreur lors de la récupération de l'URL {url}: {e}"
                    logger.exception(msg)

        visited = set()
        compteur_livres = 0
        yield from dfs(url, 0)

    def scrap(self, url, profondeur=3, nbmax=100, *args, **kwargs):
        for url_livre, mime in self.scrap_livre_generator(
            url,
            profondeur,
            nbmax,
            *args,
            **kwargs,
        ):
            self.alimenter_fichier_url(url_livre, *args, type_mime=mime, **kwargs)
