from __future__ import annotations

import abc
import contextlib
import datetime
import functools
from inspect import isabstract
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias
from zipfile import ZipFile, is_zipfile

import pikepdf
from lxml import etree

from biblio.utils import RealPath

if TYPE_CHECKING:
    from collections.abc import Iterator
    from os import PathLike

    StrPath: TypeAlias = str | PathLike[str]


def get_contenu_zip(file: StrPath, opf: StrPath) -> bytes:
    with ZipFile(file) as z:
        return z.read(str(opf))


class base_livre(abc.ABC):
    def __init__(self, ressource):
        """
        ressource désigne soit le nom de fichier (local) correspondant au livre,
        soit une URL pointant vers un livre.
        """
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def type(self):
        """renvoie le type (EPUB, PDF, ou autre) du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def titre(self):
        """renvoie le titre du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def auteur(self):
        """renvoie l'auteur du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def langue(self):
        """renvoie la langue du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def sujet(self):
        """renvoie le sujet du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    @abc.abstractmethod
    def date(self):
        """renvoie la date de publication du livre"""
        raise NotImplementedError("à définir dans les sous-classes")


class Livre(base_livre):
    """
    Classe abstraite pour les fichiers de livres.

    Les sous-classes doivent définir les méthodes suivantes:
    - auteurs, qui renvoie un liste d'auteurs
    - sujets, qui renvoie un ensemble de sujets

    On peut également redéfinir open() et close() pour ouvrir et fermer le fichier.
    La syntaxe 'with' est déjà prise en charge dans la classe abstraite.

    La sous-classe doit donner un suffixe pour le type de fichier (pdf, epub, etc.)
    en utilisant le paramètre de classe 'suffix'. Par exemple, pour les fichiers PDF,
    on définit la classe comme suit:
    ```
    class Pdf(Livre, suffix="pdf"):
        ...
    ```

    Attributs:
    - ressource: le chemin du fichier
    - SUFFIX: le suffixe du fichier (attribut de classe).

    """
    #  ici seulement pour type hinting et documentation
    SUFFIX: str  # type: ignore[misc]

    def __init_subclass__(cls, suffix=None) -> None:
        """Comme __init__ mais appelé seulement à la création de chaque sous-classe"""
        super().__init_subclass__()

        if not isabstract(cls) and suffix is None:
            msg = "Les sous-classes de Livre doivent avoir un suffixe."
            raise ValueError(msg)

        cls.SUFFIX = suffix  # type: ignore[misc]

    def __init__(self, ressource: StrPath) -> None:
        self.ressource = RealPath(ressource)

    @abc.abstractmethod
    def auteurs(self) -> list[str]: ...

    def auteur(self) -> str:
        return ",".join(self.auteurs())

    @abc.abstractmethod
    def sujets(self) -> set[str]: ...

    def sujet(self) -> str:
        return ",".join(self.sujets())

    def type(self):
        return self.SUFFIX.upper()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.ressource})"

    def open(self):
        """
        Ouvre le fichier. Doit être appelé avant d'accéder aux métadonnées du fichier,
        au risque de lever une erreur.

        Préférer l'utilisation de la syntaxe 'with' au lieu de l'appel direct à
        open() et close().
        """
        return self

    def close(self):
        """
        Ferme le fichier. Doit être appelé après avoir ouvert le fichier.
        Ne fait rien si le fichier n'est pas ouvert.
        """

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.close()


class Pdf(Livre, suffix="pdf"):
    """Classe pour les fichiers PDF."""

    """
    Les clés de métadonnées sont stockées dans un dictionnaire de listes.
    LA liste correspond à l'ordre de priorité des clés, pour un nom de clé donné.
    """
    _CLES: ClassVar = {
        "auteurs": ["dc:creator"],
        "date": ["dc:date"],
        "langue": ["dc:language"],
        "sujets": ["dc:subject", "xmp:Label", "xmpDM:genre", "pdf:Keywords"],
        "titre": ["dc:title", "xmp:Nickname"],
    }

    def __init__(self, ressource: StrPath) -> None:
        super().__init__(ressource)
        self.pdf_pike = None

    @staticmethod
    def besoin_ouverture(func):
        """
        Decorateur qui modifie la fonction pour renvoyer automatiquement une erreur
        si le fichier PDF n'est pas ouvert.
        """

        @functools.wraps(func)
        def wrapper(self: Pdf, *args, **kwargs):
            if self.pdf_pike is None:
                cls_name = self.__class__.__name__
                msg = (
                    f"Le fichier {self.ressource} n'est pas ouvert. Utiliser {cls_name}.open() ou la syntaxe 'with'"
                    f" avant d'appeler {cls_name}.{func.__name__}()."
                )
                raise ValueError(msg)
            return func(self, *args, **kwargs)

        return wrapper

    @besoin_ouverture
    def from_metadata(self, key) -> Iterator[Any]:
        return filter(bool, map(self._metadata.get, self._CLES[key]))

    def from_metadata_first(self, key) -> Any:
        return next(self.from_metadata(key), None)

    # https://github.com/adobe/XMP-Toolkit-SDK/blob/main/docs/XMPSpecificationPart1.pdf
    # https://developer.adobe.com/xmp/docs/XMPNamespaces/
    def titre(self) -> str | None:
        return self.from_metadata_first("titre") or self.ressource.stem

    def auteurs(self) -> list[str]:
        return self.from_metadata_first("auteurs") or []

    def sujet(self) -> set[str]:
        # on itère sur les valeurs renvoyées par chaque clé
        # qui peut contenir des sujets
        # et on prend dès qu'on trouve une clé qui fonctionne
        # avec dans l'ordre de priorité du plus au moins courant
        for value in self.from_metadata("sujets"):
            if value and isinstance(value, str):
                return {value}
            if isinstance(value, set):
                filter_value = set(filter(None, value))
                if filter_value:
                    return filter_value
        return set()

    def langue(self) -> set[str]:
        x = self.from_metadata_first("langue")
        if isinstance(x, str) and x:
            return {x}
        return x or set()

    def raw_date(self) -> str | None:
        return self.from_metadata_first("date")

    def date_obj(self) -> datetime.datetime | None:
        raw_date = self.raw_date()
        if raw_date is None:
            return None
        with contextlib.suppress(ValueError):
            return datetime.datetime.fromisoformat(raw_date)
        return None

    def date(self, fmt="%d/%m/%Y") -> str | None:
        date = self.date_obj()
        return date.strftime(fmt) if date else None

    def open(self):
        self.pdf_pike = pikepdf.open(self.ressource)
        self._metadata = self.pdf_pike.open_metadata()
        return self

    def close(self):
        if self.pdf_pike is None:
            return
        self.pdf_pike.close()
        self.pdf_pike = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class Epub(Livre, suffix="epub"):
    # Définition des namespaces XML pour les éléments spécifiques d'un fichier EPUB
    namespaces_xml: ClassVar = {
        "n": "urn:oasis:names:tc:opendocument:xmlns:container",
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    #  Chemin vers le dossier contenant les métadonnées d'un fichier EPUB
    meta_dir: ClassVar = "/opf:package/opf:metadata"

    def __init__(self, ressource: StrPath) -> None:
        super().__init__(ressource)

        # Les fichiers EPUB sont des archives ZIP
        if not is_zipfile(self.ressource):
            msg = "Fichier EPUB invalide"
            raise ValueError(msg)

        # Récupération du fichier container.xml, qui contient le chemin du fichier OPF
        # (le fichier OPF contient les métadonnées du livre)
        container = get_contenu_zip(self.ressource, "META-INF/container.xml")

        # Récupération du chemin du fichier OPF et de son contenu avec lxml.etree
        tree = etree.fromstring(container)  # noqa: S320
        self.opf = Path(
            self.tree_xpath("n:rootfiles/n:rootfile/@full-path", tree=tree)[0],
        )
        self.tree = etree.fromstring(get_contenu_zip(self.ressource, self.opf))  # noqa: S320

        # Récupération de la version du fichier EPUB
        self.version = self.tree_xpath("/opf:package/@version")[0]
        self.version_majeure = int(self.version[0])

    # La plupart des metadonnées sont stockées dans {meta_dir}/dc:*.
    # Voir: https://www.w3.org/TR/epub-33/#sec-metadata-values
    def from_metadata(self, key) -> str | None:
        return self.xpath_str(f"{self.meta_dir}/{key}")

    def from_metadata_list(self, key) -> list[str]:
        return self.tree_xpath_liststr(f"{self.meta_dir}/{key}")

    def titre(self):
        return self.from_metadata("dc:title")

    def auteurs(self):
        return self.from_metadata_list("dc:creator")

    def sujets(self):
        return self.from_metadata_list("dc:subject")

    def langue(self):
        return self.from_metadata("dc:language")

    def date(self):
        return self.from_metadata("dc:date")

    def xpath_str(self, path) -> str | None:
        """
        Execute une requête XPath et renvoie le texte. Assume qu'il n'y a qu'un seul élément
        correspondant à la requête. Renvoie None si aucun élément n'est trouvé.
        """
        node = self.tree_xpath(path)
        if isinstance(node, list):
            node = node[0] if node else None
        return node.text if node is not None else None

    def tree_xpath_liststr(self, path) -> list[str]:
        """
        Execute une requête XPath et renvoie une liste de texte. Il peut y avoir plusieurs
        ou aucun élément correspondant à la requête.
        """
        return [node.text for node in self.tree_xpath(path) if node is not None]

    def tree_xpath(self, path, tree: etree._Element | None = None) -> Any:
        tree = self.tree if tree is None else tree
        return tree.xpath(str(path), namespaces=self.namespaces_xml)
