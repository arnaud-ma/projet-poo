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
