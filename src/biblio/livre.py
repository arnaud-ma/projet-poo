from __future__ import annotations

import abc
import contextlib
import datetime
import functools
from inspect import isabstract
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias
from zipfile import ZipFile, is_zipfile

import pandoc
import pikepdf
from lxml import etree

if TYPE_CHECKING:
    from collections.abc import Iterator
    from os import PathLike

    StrPath: TypeAlias = str | PathLike[str]


def get_contenu_zip(file: StrPath, opf: StrPath) -> bytes:
    with ZipFile(file) as z:
        return z.read(str(opf))


class NotSupportedMimeError(NotImplementedError):
    def __init__(self, mime=""):
        m = repr(mime) if mime else ""
        self.msg = f"le type mime {m} n'est pas supporté"

    def __str__(self):
        return self.msg


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
    class Pdf(Livre, suffix="pdf", mime_type="application/pdf"):
        ...
    ```

    Attributs:
    - ressource: le chemin du fichier
    - is_open: un booléen pour savoir si le fichier est ouvert ou non
    - TYPE_MIME: le type MIME du fichier (attribut de classe)
    - SUFFIX: le suffixe du fichier (attribut de classe)
    - TYPES_MIME: un dictionnaire contenant les types MIME des sous-classes de Livre
        (attribut commun à toutes les sous-classes)
    - SUFFIXES: un dictionnaire contenant les suffixes des sous-classes de Livre
        (attribut commun à toutes les sous-classes)
    """

    #  ici seulement pour type hinting et documentation
    TYPE_MIME: ClassVar[str]
    TYPES_MIME: ClassVar[dict[str, type[Livre]]] = {}
    SUFFIX: ClassVar[str]
    SUFFIXES: ClassVar[dict[str, type[Livre]]] = {}

    def __init_subclass__(
        cls,
        suffix: str | None = None,
        mime_type: str | None = None,
    ) -> None:
        """Comme __init__ mais appelé seulement à la création de chaque sous-classe"""
        super().__init_subclass__()

        if isabstract(cls):
            return
        if mime_type is None or suffix is None:
            msg = "Les sous-classes de Livre doivent avoir un suffixe et un type MIME."
            raise ValueError(msg)

        cls.SUFFIX = suffix  # type: ignore[misc]
        cls.SUFFIXES[suffix] = cls  # type: ignore[misc]
        cls.TYPES_MIME[mime_type] = cls  # type: ignore[misc]
        cls.TYPE_MIME = cls  # type: ignore[misc]

    def __init__(self, ressource: StrPath) -> None:
        self.ressource = Path(ressource)
        self.is_open = False

    def __fspath__(self):
        """Renvoie le chemin du fichier. Utilisé par open(), Path(), etc."""
        return str(self.ressource)

    @classmethod
    def depuis_mime_type(cls, mime_type: str):
        if mime_type not in cls.TYPES_MIME:
            raise NotSupportedMimeError(mime_type)
        return cls.TYPES_MIME[mime_type]

    def type(self):
        return self.SUFFIX.upper()

    @abc.abstractmethod
    def auteurs(self) -> list[str]: ...

    def auteur(self) -> str:
        return ",".join(self.auteurs())

    @abc.abstractmethod
    def sujets(self) -> set[str]: ...

    def sujet(self) -> str:
        return ",".join(self.sujets())

    @abc.abstractmethod
    def date_obj(self) -> datetime.datetime | None: ...

    def date(self, fmt="%d/%m/%Y") -> str | None:
        date = self.date_obj()
        return date.strftime(fmt) if date else None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.ressource})"

    def __str__(self):
        try:
            x = self.titre()
        except (ValueError, NotImplementedError):
            x = self.ressource.stem
        else:
            if x is None:
                x = self.ressource.name
        return x

    def rapport_livre_markdown(
        self,
        content=("titre", "auteur", "type"),
        start="## ",
        end="",
        if_falsy="Non renseigné",
    ):
        """
        Renvoie un rapport en format markdown pour le livre.

        Args:
          - content: une liste de noms de méthodes à appeler (dans le même ordre)
            pour obtenir le contenu du rapport. Chaque nom de méthode doit exister
            dans la classe sinon une erreur sera levée. Par défaut, ("titre", "auteur", "type").
          - start: le texte à ajouter au début du rapport. Par défaut, un titre de niveau 2 (##).
          - end: le texte à ajouter à la fin du rapport. Par défaut, une chaîne vide.
          - if_falsy: la valeur à afficher si le contenu est vide. Par défaut, "Non renseigné".
        """
        content = {func_name: getattr(self, func_name)() for func_name in content}
        content_str = "\n".join(
            f"- **{key}** : {value or if_falsy}" for key, value in content.items()
        )
        return f"{start}{self.ressource.name} \n\n{content_str}{end}"

    @abc.abstractmethod
    def write_from_markdown(self, content_markdown: str, /):
        """Transforme le contenu markdown en un fichier du type du livre et l'écrit.

        Exemple:
        ```
        mon_livre = Pdf("mon_livre.pdf")
        mon_livre.write_from_markdown("# Titre de mon livre sous format PDF")
        ```
        """


def besoin_metadata(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.already_init:
            self._init_meta()
        return func(self, *args, **kwargs)

    return wrapper


class Pdf(Livre, suffix="pdf", mime_type="application/pdf"):
    """Classe pour les fichiers PDF."""

    # Les clés de métadonnées sont stockées dans un dictionnaire de listes.
    # La liste correspond à l'ordre de priorité des clés, pour un nom de clé donné.
    # Pour savoir d'où viennent le nom des clés, voir:
    # https://github.com/adobe/XMP-Toolkit-SDK/blob/main/docs/XMPSpecificationPart1.pdf
    # https://developer.adobe.com/xmp/docs/XMPNamespaces/
    _CLES_METADATA: ClassVar = {
        "auteurs": ["dc:creator"],
        "date": ["dc:date"],
        "langue": ["dc:language"],
        "sujets": ["dc:subject", "xmp:Label", "xmpDM:genre", "pdf:Keywords"],
        "titre": ["dc:title", "xmp:Nickname"],
    }

    def __init__(self, ressource: StrPath) -> None:
        super().__init__(ressource)
        self.already_init = False

    def _init_meta(self):
        self.already_init = True
        self.pdf_pike = pikepdf.Pdf.open(self.ressource)
        self._metadata = self.pdf_pike.open_metadata()

    @besoin_metadata
    def from_metadata(self, key) -> Iterator[Any]:
        return filter(bool, map(self._metadata.get, self._CLES_METADATA[key]))

    def from_metadata_first(self, key) -> Any:
        return next(self.from_metadata(key), None)

    def titre(self) -> str | None:
        return self.from_metadata_first("titre") or self.ressource.stem

    def auteurs(self) -> list[str]:
        extracted_authors = self.from_metadata("auteurs")
        # extracted est de type is Iterable[str | list[str]]
        # il faut le transformer en une liste de str
        if not extracted_authors:
            return []
        result = []
        for author in extracted_authors:
            if isinstance(author, str):
                result.append(author)
            elif isinstance(author, list):
                result.extend(author)

        # supprime les doublons tout en conservant l'ordre
        return list(dict.fromkeys(result))

    def sujets(self) -> set[str]:
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
        """Renvoie la date de publication du fichier PDF sous forme de chaîne de caractères,
        avec un format qui est défini par le pdf lui-même."""
        return self.from_metadata_first("date")

    def date_obj(self) -> datetime.datetime | None:
        """Renvoie la date de publication du fichier PDF sous forme d'objet datetime."""
        raw_date = self.raw_date()
        if raw_date is None:
            return None
        with contextlib.suppress(ValueError):
            return datetime.datetime.fromisoformat(raw_date)
        return None

    def write_from_markdown(self, content: str):
        doc = pandoc.read(content, format="markdown")
        pandoc.write(doc, self.ressource, format="pdf")


class Epub(Livre, suffix="epub", mime_type="application/epub+zip"):
    # Définition des namespaces XML pour les éléments spécifiques d'un fichier EPUB
    NAMESPACES_XML: ClassVar = {
        "n": "urn:oasis:names:tc:opendocument:xmlns:container",
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    #  Chemin vers le dossier contenant les métadonnées d'un fichier EPUB
    META_DIR: ClassVar = "/opf:package/opf:metadata"

    def __init__(self, ressource: StrPath) -> None:
        super().__init__(ressource)
        self.already_init = False

    def _init_meta(self):
        self.already_init = True
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
        return self.xpath_str(f"{self.META_DIR}/{key}")

    def from_metadata_list(self, key) -> list[str]:
        return self.tree_xpath_liststr(f"{self.META_DIR}/{key}")

    def titre(self):
        return self.from_metadata("dc:title")

    def auteurs(self):
        return self.from_metadata_list("dc:creator")

    def sujets(self):
        return self.from_metadata_list("dc:subject")

    def langue(self):
        return self.from_metadata("dc:language")

    def raw_date(self) -> str | None:
        return self.from_metadata("dc:date")

    def date_obj(self) -> datetime.datetime | None:
        """Renvoie la date de publication du fichier PDF sous forme d'objet datetime."""
        raw_date = self.raw_date()
        if raw_date is None:
            return None
        with contextlib.suppress(ValueError):
            return datetime.datetime.fromisoformat(raw_date)
        return None

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

    @besoin_metadata
    def tree_xpath(self, path, tree: etree._Element | None = None) -> Any:
        tree = self.tree if tree is None else tree
        return tree.xpath(str(path), namespaces=self.NAMESPACES_XML)

    def write_from_markdown(self, content: str):
        doc = pandoc.read(content, format="markdown")
        pandoc.write(doc, self.ressource, format="epub")
