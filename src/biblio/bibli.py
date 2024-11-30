import shutil
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


class simple_bibli(base_bibli):
    path: RealPath

    def __init__(self, path: StrPath):
        p = Path(path)
        if not p.exists():
            p.mkdir()
        self.path = RealPath(p)
        self._livres = set()
        self.update_livres()

    def livres_gen(self):
        return (x for x in Path(self.path).glob("*") if x.is_file())

    def update_livres(self):
        self._livres = set(self.livres_gen())

    def ajouter(self, livre):
        nom = Path(livre).name
        shutil.copy2(livre, self.path / nom)
        self._livres.add(livre)

    def rapport_auteurs(self, format, fichier):
        Livre.SUFFIXES[format](fichier).ecrit_rapport([{
            
        }])

    def __iter__(self):
        return iter(self._livres)

    def __contains__(self, livre):
        return livre in set(self._livres)

    def __len__(self):
        return len(self._livres)

    def add(self, livre):
        return self.ajouter(livre)

    def discard(self, livre, *, remove_from_disk=False):
        if (
            remove_from_disk
            and livre in self
            and (p := Path(livre)).exists()
            and p.is_file()
        ):
            p.unlink()
        self._livres.discard(livre)


if __name__ == "__main__":
    biblio = simple_bibli("temp")
    for livre in biblio._livres:
        print(livre)
