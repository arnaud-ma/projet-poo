from __future__ import annotations

import abc
import datetime
from inspect import isabstract
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import ebookmeta
import pymupdf

if TYPE_CHECKING:
    from os import PathLike

    StrPath: TypeAlias = str | PathLike[str]


class RealPath(Path):
    """Comme Path mais lance une ValueError si le fichier n'existe pas"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.exists():
            msg = f"Le chemin {self} n'existe pas."
            raise ValueError(msg)


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
    #  ici seulement pour type hinting et documentation
    SUFFIX: str  # type: ignore[misc]

    def __init_subclass__(cls, suffix=None) -> None:
        """Comme __init__ mais appelé seulement à la création de chaque sous-classe"""
        super().__init_subclass__()

        if not isabstract(cls) and suffix is None:
            msg = "Les sous-classes de Livre doivent avoir un suffixe."
            raise ValueError(msg)

        cls.SUFFIX = suffix

    def __init__(self, ressource: StrPath) -> None:
        self.ressource = RealPath(ressource)
        self._fichier = None

    def type(self):
        return self.SUFFIX.upper()


class PDF(Livre, suffix="pdf"):
    def __init__(self, ressource: StrPath) -> None:
        super().__init__(ressource)
        self.reader = pymupdf.open(self.ressource)
        self._metadata = self.reader.metadata or {}

    def from_metadata(self, key):
        return self._metadata.get(key, None)

    # fmt: off
    def titre(self): return self.from_metadata("title")
    def auteur(self): return self.from_metadata("author")
    def sujet(self): return self.from_metadata("subject")
    def langue(self): return None  # noqa: PLR6301
    # fmt: on

    def date_obj(self):
        raw_pdf_date = self.from_metadata("creationDate")
        if not raw_pdf_date:
            return None
        date = raw_pdf_date[2:10]
        # TODO: gerer les timezone (utc + 2 ou autre)
        return datetime.datetime.strptime(date, "%Y%m%d")  # noqa: DTZ007

    def date(self):
        date = self.date_obj()
        return date.strftime("%d/%m/%Y") if date else None


class EPUB(Livre, suffix="epub"):
    def __init__(self, ressource: StrPath):
        super().__init__(ressource)
        # besoin de convertir en str puisque ebookmeta ne supporte pas Path
        self._metadata = ebookmeta.get_metadata(str(self.ressource))

    def titre(self):
        return self._metadata.title or None

    def auteur(self):
        return ",".join(self._metadata.author_list) or None

    def sujet(self):
        return ",".join(self._metadata.tag_list) or None

    def langue(self):
        return self._metadata.lang

    def date(self):
        # TODO
        return self._metadata.publish_info.year
