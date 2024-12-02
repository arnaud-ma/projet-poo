import mimetypes
import shutil
import textwrap
from collections import defaultdict
from io import StringIO
from pathlib import Path

from biblio.livre import Livre
from biblio.utils import RealPath, StrPath


class base_bibli:
    def __init__(self, path):
        """path désigne le répertoire contenant les livres de cette bibliothèque"""
        raise NotImplementedError("à définir dans les sous-classes")

    def ajouter(self, livre):
        """
        Ajoute le livre à la bibliothèque"""
        raise NotImplementedError("à définir dans les sous-classes")

    def rapport_livres(self, format, fichier):
        """
        Génère un état des livres de la bibliothèque.
        Il contient la liste des livres,
        et pour chacun d'eux
        son titre, son auteur, son type (PDF ou EPUB), et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
        """
        raise NotImplementedError("à définir dans les sous-classes")

    def rapport_auteurs(self, format, fichier):
        """
        Génère un état des auteurs des livres de la bibliothèque.
        Il contient pour chaque auteur
        le titre de ses livres en bibliothèque et le nom du fichier correspondant au livre.
        le type (PDF ou EPUB),
        et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
        """
        raise NotImplementedError("à définir dans les sous-classes")


class simple_bibli(set[Livre], base_bibli):
    def __init__(self, path: StrPath, max_livres: int = 1000):
        super().__init__()
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        self.path = RealPath(p)
        self.max_livres = max_livres
        self.update_livres()

    def livres_gen(self):
        return (
            Livre.depuis_mime_type(mime_type)(file)
            for file in Path(self.path).glob("*")
            if file.is_file()
            and ((mime_type := mimetypes.guess_type(file)[0]) is not None)
        )

    def update_livres(self):
        for livre in self.livres_gen():
            if len(self) > self.max_livres:
                return
            self.add(livre)

    def add(self, livre):
        return self.ajouter(livre)

    def ajouter(self, livre):
        nom = Path(livre).name
        if len(self) > self.max_livres:
            return
        if not (self.path / nom).exists():
            shutil.copy2(livre, self.path / nom)
        super().add(livre)

    def rapport_livres(self, format, fichier):
        result = StringIO()
        result.write("# Rapport des livres\n\n")

        for livre in self:
            result.write(livre.rapport_livre_markdown(end="\n\n"))

        livre_rapport = Livre.SUFFIXES[format](fichier)
        livre_rapport.write_from_markdown(result.getvalue())

    def get_auteurs(self):
        auteurs: defaultdict[str | None, set[Livre]] = defaultdict(set)
        for livre in self:
            for auteur in livre.auteurs():
                auteurs[auteur].add(livre)
        return auteurs

    @staticmethod
    def rapport_auteur_markdown(auteur, livres):
        result = StringIO()
        result.write(f"## {auteur}\n\n")
        for livre in livres:
            rapport_livre = livre.rapport_livre_markdown(
                content=("titre", "type"),
                start="- ### ",
                end="\n\n",
            )

            # on indente pour avoir une liste à puce de niveau 2:
            # ## auteur
            # - ### titre
            #   - type
            #   - ...

            # strip() pour enlever l'indentation du début
            rapport_livre = textwrap.indent(rapport_livre, "  ").strip()

            result.write(rapport_livre)
            result.write("\n")
        return result.getvalue()

    def rapport_auteurs(self, format, fichier):
        auteurs = self.get_auteurs()
        result = StringIO()
        result.write("# Rapport des auteurs\n\n")

        for auteur, livres in auteurs.items():
            result.write(self.rapport_auteur_markdown(auteur, livres))
            result.write("\n")

        livre_rapport = Livre.SUFFIXES[format](fichier)
        livre_rapport.write_from_markdown(result.getvalue())

    def discard(self, livre, *, remove_from_disk=False):
        if (
            remove_from_disk
            and livre in self
            and (p := Path(livre)).exists()
            and p.is_file()
        ):
            p.unlink()
        super().discard(livre)


if __name__ == "__main__":
    biblio = simple_bibli("temp/", max_livres=10)
    # biblio.rapport_livres("pdf", "rapport.pdf", progressbar=True)
    biblio.rapport_livres("pdf", "rapport_auteurs.pdf")
    print(biblio.get_auteurs())
